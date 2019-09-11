# We are assuming that blocks are 0 indexed everywhere
import logging
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
		
		#-------------CRITICAL-------------
		self.log_array = []                     # This would maintain all write operations from the beginning, to help us checkpoint
		self.checkpoints = []					# Each checkpoint would be a copy of the log_array existing during the time of checkpointing
		#----------CRITICAL END-------------


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
			
	def write(self, block_num, data, log=True):
		# This function will call read_physical_block and write_physical_block
		# after figuring out the correct virtual block number
		# when log is true I log the data on the log file
		if block_num >= self.num_blocks:
			raise Exception("Error : Block number out of bounds")
		else:
			for i in self.fragment:
				if i.num_blocks > block_num:
					virtual_address = i.starting_block + block_num
					success, error = write_physical_block(virtual_address, data)
					if(success):
						#write to log array
						if(log):
							self.log_array.append((block_num, data))
					else:
						raise Exception(error)
				block_num -= i.num_blocks
			# raise Exception("Error : Some unknown write error occurred")

	#------------CHECKPOINTING FUNCTIONS------------
	def create_checkpoint(self):
		self.checkpoints.append(self.log_array.copy())
		return len(self.checkpoints)-1

	def restore_checkpoint(self,cpt):
		#restore the disk state at checkpoint index cpt from the array self.checkpoints
		# Step 1: Write empty string on all blocks of this disk
		for i in range(self.num_blocks):
			self.write(i,"",False)
		# Step 2: Restore state
		if(cpt>=len(self.checkpoints)):
			raise Exception("Error: checkpoint id not valid")
		writes_to_do = self.checkpoints[cpt]
		for block_num, data in writes_to_do:
			self.write(block_num,data,False)
		# Step 3: Replace current log file to checkpointed log file
		self.log_array = self.checkpoints[cpt].copy()



# User level APIs for checkpointing
def create_checkpoint(id):
	global disks
	if id in disks:
		return disks[id].create_checkpoint()
	else:
		raise Exception("Error : Disk ID not present")
def restore_checkpoint(id,cpt):
	global disks
	if id in disks:
		disks[id].restore_checkpoint(cpt)
	else:
		raise Exception("Error : Disk ID not present")
		
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
	#returns (Success:bool, error_message:string)
	global virtual_to_physical
	if block_num < 500 and block_num >= 0 and len(block_info) <= 100:
		virtual_to_physical[block_num].data = block_info
		return (True,"")
	elif len(block_info) > 100:
		return (False,"Error : Data to write exceeds block size")
		# raise Exception("Error : Data to write exceeds block size") 
	else:
		return (False,"Error : Block number out of bounds")
		# raise Exception("Error : Block number out of bounds") 

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


def test_checkpoints():
	create_disk("c",100)

	write_block("c",1,"1")
	print("write(1,1)")
	write_block("c",2,"2")
	print("write(2,2)")
	cpt1 = create_checkpoint("c")
	print("---------CHECKPOINT cpt1 CREATE at C-------------")
	write_block("c",2,"3")
	print("write(2,3)")
	cpt2 = create_checkpoint("c")
	print("---------CHECKPOINT cpt2 CREATE at C-------------")

	restore_checkpoint("c",cpt1)
	print("---------CHECKPOINT cpt1 RESTORED at C-------------")
	print("Data at block 2 on c is: "+read_block("c",2))

	restore_checkpoint("c",cpt2)
	print("---------CHECKPOINT cpt2 RESTORED at C-------------")
	print("Data at block 2 on c is: "+read_block("c",2))

	write_block("c",2,"4")
	print("write(2,4)")
	cpt3 = create_checkpoint("c")
	print("--------CHECKPOINT cpt3 CREATED at C---------------")

	restore_checkpoint("c",cpt1)
	print("---------CHECKPOINT cpt1 RESTORED at C-------------")
	print("Data at block 2 on c is: "+read_block("c",2))

	restore_checkpoint("c",cpt3)
	print("---------CHECKPOINT cpt3 RESTORED at C-------------")
	print("Data at block 2 on c is: "+read_block("c",2))

test_checkpoints()