# We are assuming that blocks are 0 indexed everywhere

class Block:
	def __init__(self):
		self.data = ''

# A class whose objects we will create 
# The starting block number stored here is the virtual block number of 500 sized disk
class Fragments:
	def __init__(self, starting_block, num_blocks):
		self.starting_block = starting_block
		self.num_blocks = num_blocks

# A class whose object we will create for each virtual disk
class Disk:
	def __init__(self, blockId, num_blocks, fragment):
		self.blockId = blockId					# BlockID of this disk
		self.num_blocks = num_blocks			# Number of blocks in this virtual disk
		self.fragment = fragment				# A list of fragments for this virtual disk

	def read(self, block_num):
		# This function will call read_physical_block and write_physical_block
		# after figuring out the correct virtual block number
		if block_num >= self.num_blocks:
			raise Exception("Error : Block number out of bounds")
		else:
			for i in self.fragment:
				if i.num_blocks > block_num:
					virtual_address = i.starting_block + block_num
					return read_physical_block(virtual_address)
				block_num -= i.num_blocks
			raise Exception("Error : Some unknown read error occurred")
			
	def write(self, block_num, data):
		# This function will call read_physical_block and write_physical_block
		# after figuring out the correct virtual block number
		if block_num >= self.num_blocks:
			raise Exception("Error : Block number out of bounds")
		else:
			for i in self.fragment:
				if i.num_blocks > block_num:
					virtual_address = i.starting_block + block_num
					return write_physical_block(virtual_address, data)
				block_num -= i.num_blocks
			raise Exception("Error : Some unknown write error occurred")
		
# I/O on smaller virtual user created disks. User level APIs
def read_block(id, block_num):
	global disks
	if id in disks:
		return disks[id].read(block_num)
	else:
		raise Exception("Error : Disk ID not present")

def write_block(id, block_num, block_info):
	global disks
	if id in disks:
		return disks[id].write(block_num, block_info)
	else:
		raise Exception("Error : Disk ID not present")

# I/O on global virtual disk of 500 size. Lowest level APIs
def read_physical_block(block_num):
	global virtual_to_physical
	if block_num < 500 and block_num >= 0:
		return virtual_to_physical[block_num].data
	else:
		raise Exception("Error : Block number out of bounds") 

def write_physical_block(block_num, block_info):
	global virtual_to_physical
	if block_num < 500 and block_num >= 0 and len(block_info) <= 100:
		virtual_to_physical[block_num].data = block_info
	elif len(block_info) > 100:
		raise Exception("Error : Data to write exceeds block size") 
	else:
		raise Exception("Error : Block number out of bounds") 

# Create disk and allocate its fragments from global_fragments_list
def create_disk(id, num_blocks):
	global global_fragments_list
	global disks
	if id not in disks:
		allocated = False
		fragment = []
		total_space_left = 0
		for i in range(len(global_fragments_list)):
			total_space_left += global_fragments_list[i].num_blocks

			if global_fragments_list[i].num_blocks == num_blocks:
				fragment.append(global_fragments_list[i])
				allocated = True
				global_fragments_list.pop(count)
				break
			elif global_fragments_list[i].num_blocks > num_blocks:
				global_fragments_list[i].num_blocks -= num_blocks
				fragment.append(Fragments(global_fragments_list[i].starting_block+global_fragments_list[i].num_blocks ,num_blocks))
				allocated = True
				break

		required = num_blocks
		if (not allocated) and (total_space_left >= required):
			for i in range(len(global_fragments_list)-1, -1, -1):
				if required > 0:
					if global_fragments_list[i].num_blocks <= required:
						fragment.append(global_fragments_list[i])
						global_fragments_list.pop(i)
					else:
						global_fragments_list[i].num_blocks -= required
						fragment.append(Fragments(global_fragments_list[i].starting_block+global_fragments_list[i].num_blocks ,required))
				else:
					break
		elif total_space_left < required:
			raise Exception("Error : Not enough space left to create disk of this size") 

		my_obj = Disk(id, num_blocks, fragment)
		disks[id] = my_obj
	else:
		raise Exception("Error : Disk ID already exists") 

# Delete disk and merge fragments in global_fragments_list
def delete_disk(id):
	global disks
	global global_fragments_list
	obj = disks[id]
	# print(len(obj.fragment))
	for fragment in obj.fragment:
		leng = len(global_fragments_list)
		end_tf = fragment.starting_block + fragment.num_blocks

		if leng > 0:
			for j in range(leng):
				if global_fragments_list[j].starting_block > end_tf:
					if j > 0:
						prev_end_tf = global_fragments_list[j-1].starting_block+global_fragments_list[j-1].num_blocks
						if prev_end_tf == fragment.starting_block:
							global_fragments_list[j-1].num_blocks += fragment.num_blocks
						else:
							global_fragments_list.insert(j-1, fragment)
					else:
						global_fragments_list.insert(0, fragment)
					break	
				elif global_fragments_list[j].starting_block == end_tf:
					if j > 0:
						prev_end_tf = global_fragments_list[j-1].starting_block+global_fragments_list[j-1].num_blocks
						if prev_end_tf == fragment.starting_block:
							global_fragments_list[j-1].num_blocks += fragment.num_blocks+global_fragments_list[j].num_blocks
							global_fragments_list.pop(j)
						else:
							global_fragments_list[j].starting_block = fragment.starting_block
							global_fragments_list[j].num_blocks += fragment.num_blocks
					else:
						global_fragments_list[j].starting_block = fragment.starting_block
						global_fragments_list[j].num_blocks += fragment.num_blocks
					break	
				else: 
					if j == leng-1:
						prev_end_tf = global_fragments_list[j].starting_block+global_fragments_list[j].num_blocks
						if prev_end_tf == fragment.starting_block:
							global_fragments_list[j].num_blocks += fragment.num_blocks
						else:
							global_fragments_list.append(fragment)
						break
		else:
			global_fragments_list.append(fragment)

	del(disks[id])


block_size = 100
diskA = [Block() for i in range(200)]
diskB = [Block() for i in range(300)]
disks = {}		# A dictionary from diskID to Disk Object
global_virtual_disk_size = (len(diskA)+len(diskB))

# We will use this list to allocate fragments to each smaller virtual disk
global_fragments_list = [Fragments(0, 500)]

# A mapping from virtual block number to the original block of the physical diskA or B
virtual_to_physical = {}
for i in range(global_virtual_disk_size):
	if i < len(diskA):
		virtual_to_physical[i] = diskA[i]
	else:
		virtual_to_physical[i] = diskB[i-len(diskA)]


def testReadWritePhysical():
	try:
		print("-----writing Atishya Jain at block 345")
		write_physical_block(345,"Atishya Jain")
	except Exception as e:
		print(e)

	try:
		print("-----writing Mankaran Singh at block 145")
		write_physical_block(145,"Mankaran Singh")
	except Exception as e:
		print(e)

	try:
		print("-----writing Avaljot Singh at block 500")
		write_physical_block(500,"Avaljot Singh")
	except Exception as e:
		print(e)

	try:
		print("-----writing Mayank Singh Chauhan at block 82")
		write_physical_block(82,"Mayank Singh Chauhan")
	except Exception as e:
		print(e)
	
	print("-----reading block 145")
	print(read_physical_block(145))

	try:
		print("-----reading block 500")
		print(read_physical_block(500))
	except Exception as e:
		print(e)

	print("-----reading block 82")
	print(read_physical_block(82))
	print("-----reading block 345")
	print(read_physical_block(345))

	try:
		print("-----reading block -23")
		print(read_physical_block(-23))
	except Exception as e:
		print(e)
	print("-----reading block 121")
	print(read_physical_block(121))

def testDiskCreation():
	global global_fragments_list
	for i in range(4):
		create_disk(i,50)
		print("-----creating disk "+str(i)+" of size 50-----")
		print("-----prinitng fragments-----")
		print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	delete_disk(1)
	print("-----deleting disk 1-----")
	print("-----prinitng fragments-----")
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	delete_disk(3)
	print("-----deleting disk 3-----")
	print("-----prinitng fragments-----")
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	for i in range(3):
		create_disk(i+10,100)
		print("-----creating disk "+str(i+10)+" of size 100-----")
		print("-----prinitng fragments-----")
		print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	create_disk(5,100)
	print("-----creating disk 5 of size 100-----")
	print("-----prinitng fragments-----")	
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	delete_disk(5)
	print("-----deleting disk 5-----")
	print("-----prinitng fragments-----")
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	delete_disk(12)
	print("-----deleting disk 12-----")
	print("-----prinitng fragments-----")
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	delete_disk(11)
	print("-----deleting disk 11-----")
	print("-----prinitng fragments-----")
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	delete_disk(10)
	print("-----deleting disk 10-----")
	print("-----prinitng fragments-----")
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	delete_disk(2)
	print("-----deleting disk 2-----")
	print("-----prinitng fragments-----")
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	delete_disk(0)
	print("-----deleting disk 0-----")
	print("-----prinitng fragments-----")
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])

def testReadWriteVirtual():
	create_disk(0,400)
	print("-----creating disk 0 of size 400-----")
	print("-----prinitng fragments-----")
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	write_block(0,58,"Mayank Singh Chauhan")
	print("-----write Mayank Singh Chauhan at disk 0 at block 58-----")
	print("-----read at disk 0 at block 58-----")
	print(read_block(0,58))
	create_disk(1,99)
	print("-----creating disk 1 of size 99-----")
	write_block(1,58,"Mankaran Singh")
	print("-----write Mankaran Singh at disk 1 at block 58-----")
	print("-----read at disk 1 at block 58-----")
	print(read_block(1,58))
	print("-----prinitng fragments-----")
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	delete_disk(1)
	print("-----delete disk 1-----")
	print("-----prinitng fragments-----")
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])

print("----------TEST READ WRITE PHYSICAL BEGIN--------")
testReadWritePhysical()
print("----------TEST READ WRITE PHYSICAL END--------")
print("----------TEST DISK CREATION BEGIN--------")
testDiskCreation()
print("----------TEST DISK CREATION END--------")
print("----------TEST READ WRITE VIRTUAL BEGIN--------")
testReadWriteVirtual()
print("----------TEST READ WRITE VIRTUAL END--------")