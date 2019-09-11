# We are assuming that blocks are 0 indexed everywhere
import random

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
		self.badBlocks = []
		self.meToCopy = {}

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
def read_block1(id, block_num):
	global disks
	if id in disks:
		return disks[id].read(block_num)
	else:
		raise Exception("Error : Disk ID not present")

def write_block1(id, block_num, block_info):
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
def create_disk1(id, num_blocks):
	# num_blocks = num_blocks*2
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
						required -= global_fragments_list[i].num_blocks
						global_fragments_list.pop(i)
					else:
						global_fragments_list[i].num_blocks -= required
						required = 0
						fragment.append(Fragments(global_fragments_list[i].starting_block+global_fragments_list[i].num_blocks ,required))
				else:
					break
		elif total_space_left < required:
			raise Exception("Error : Not enough space left to create disk of this size") 

		my_obj = Disk(id, num_blocks, fragment)
		disks[id] = my_obj
	else:
		raise Exception("Error : Disk ID already exists") 

def allot(c):
	global global_fragments_list
	# sort(c)
	for i in range(len(c)):
		for j in range(len(global_fragments_list)):
			if(global_fragments_list[j].starting_block == c[i]):
				if(global_fragments_list[j].num_blocks == 1):
					global_fragments_list.pop(j)
					break
				else:
					global_fragments_list[j].starting_block += 1
					global_fragments_list[j].num_blocks -= 1
					break
			elif(global_fragments_list[j].starting_block < c[i]):
				if(global_fragments_list[j].starting_block + global_fragments_list[j].num_blocks - 1 > c[i]):
					xxx = global_fragments_list[j].num_blocks
					global_fragments_list[j].num_blocks = c[i] - global_fragments_list[j].starting_block
					global_fragments_list.insert(j+1,Fragments(c[i]+1, global_fragments_list[j].starting_block + xxx-c[i] - 1))
					break
				elif(global_fragments_list[j].starting_block + global_fragments_list[j].num_blocks - 1 == c[i]):
					global_fragments_list[j].num_blocks -= 1
					break


# Delete disk and merge fragments in global_fragments_list
def delete_disk1(id):
	global disks
	global global_fragments_list
	obj = disks[id]
	c = []
	for j in disks[id].badBlocks:
		l = j
		for i in disks[id].fragment:
			if i.num_blocks > l:
				c.append(i.starting_block + l)
			l -= i.num_blocks
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
	allot(c)

def create_disk(id,num_blocks):
	total_space_left = 0
	global global_fragments_list
	global disks
	for i in range(len(global_fragments_list)):
		total_space_left += global_fragments_list[i].num_blocks
	if(total_space_left >= 2*num_blocks):
		create_disk1(id,num_blocks)
		print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
		create_disk1(str(id),num_blocks)
	else:
		raise Exception("Error : Not Enough Space")

def read_block(id,block_num):
	a = random.randint(1,100)
	global disks
	global iniPointer
	if(block_num in disks[id].badBlocks):
		print("Original Location Corrupted")
		try:
			return read_block1(str(id),block_num)
		except Exception as e:
			print(e)
	else:		
		if(a>9):
			try:
				return read_block1(id,block_num)
			except Exception as e:
				print(e)
		else:
			print("Block is corrupted")
			try:
				isAvail = False
				xx = read_block1(str(id),block_num)
				if(copyDisk[iniPointer] == False):
					raise Exception("Error: 10 percent of disk is corrupted")
				disks[id].badBlocks.append(block_num)
				disks[id].meToCopy[block_num] = iniPointer
				write_block1(-1,iniPointer,xx)
				copyDisk[iniPointer] = False
				for i in range(50):
					iniPointer = (iniPointer+1+i)%(50)
					if(copyDisk[iniPointer]==True):
						isAvail = True
						break;
				if(isAvail==True):
					return xx
				else:
					raise Exception("Error: 10 percent of disk is corrupted")
			except Exception as e:
				print(e)

def write_block(id,block_num,block_info):
	try:
		write_block1(id,block_num,block_info)
		write_block1(str(id),block_num,block_info)
	except Exception as e:
		print(e)

def delete_disk(id):
	try:
		delete_disk1(id)
		delete_disk1(str(id))
	except Exception as e:
		print(e)

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

create_disk1(-1,50)
iniPointer = 0
copyDisk = [True for i in range(50)]

def Testing():
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	create_disk(0,200)
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	write_block(0,0,"Atishya Jain")
	write_block(0,99,"Mankaran Singh")
	write_block(0,199,"Mayank Singh Chauhan")
	print(read_block(0,0))
	# print(read_block(0,0))
	delete_disk(0)
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])
	create_disk(1,200)
	print([(j.starting_block, j.num_blocks) for j in global_fragments_list])

Testing()