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
	def __init__(self, blockId, num_blocks, fragment, fragment_size):
		self.blockId = blockID					# BlockID of this disk
		self.num_blocks = num_blocks			# Number of blocks in this virtual disk
		self.fragment = fragment				# A list of fragments for this virtual disk
		self.fragment_size = fragment_size		# A list of fragment sizes for this virtual disk

	def read(self, block_num):
		# This function will call read_physical_block and write_physical_block
		# after figuring out the correct virtual block number
		pass

	def write(self, block_num, data):
		# This function will call read_physical_block and write_physical_block
		# after figuring out the correct virtual block number
		pass
		
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

def create_disk():
	# Create disk and allocate its fragments from global_fragments_list
	pass

def delete_disk(id):
	# Delete disk and merge fragments in global_fragments_list
	pass


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
