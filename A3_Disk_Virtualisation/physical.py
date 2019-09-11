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
		self.blockId = blockID					# BlockID of this disk
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
					if global_fragments_list.num_blocks <= required:
						fragment.append(global_fragments_list[i])
						global_fragments_list.pop(i)
					else:
						global_fragments_list[i].num_blocks -= required
						fragment.append(Fragments(global_fragments_list[i].starting_block+global_fragments_list[i].num_blocks ,required))
				else:
					break
		else:
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
	for fragment in obj.fragment:
		leng = len(global_fragments_list)
		end_tf = fragment.starting_block + fragment.num_blocks
		for j in range(leng):
			if global_fragments_list[j].starting_block > end_tf:
				if j > 0:
					prev_end_tf = global_fragments_list[j-1].starting_block+global_fragments_list[j-1].num_blocks
					if prev_end_tf == fragment.starting_block:
						global_fragments_list[j-1].num_blocks += fragment.num_blocks
					else:
						global_fragments_list.insert(j-1, fragment)
				else:
					global_fragments_list.insert(fragment)
			elif global_fragments_list[j].starting_block == end_tf:
				if j > 0:
					prev_end_tf = global_fragments_list[j-1].starting_block+global_fragments_list[j-1].num_blocks
					if prev_end_tf == fragment.starting_block:
						global_fragments_list[j-1].num_blocks += fragment.num_blocks
					else:
						global_fragments_list.insert(j-1, fragment)
				else:
					global_fragments_list[j].starting_block = fragment.starting_block
					global_fragments_list[j].num_blocks += fragment.num_blocks
			else: 
				if j == leng-1:
					prev_end_tf = global_fragments_list[j].starting_block+global_fragments_list[j].num_blocks
					if prev_end_tf == fragment.starting_block:
						global_fragments_list[j].num_blocks += fragment.num_blocks
					else:
						global_fragments_list.append(fragment)
	disks[id] = None


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
