import random
import string
import os

"""
Main
"""
print("NOTICE: If you still have licenses in your license list.txt file, "
      "then those will be invalidated if more are generated.")
print("----------------------------------------------------------")

# Receive User Input
print("How many members licenses would you like to generate?")
amt = int(input())

# Write/Create new File if not there + Generate Active Licenses
f = open("license list.txt", "w+")
c = 0
while c < amt:
    val = ''.join(random.choices(string.ascii_letters + string.digits, k=30))
    print(val)
    f.write(val + "\n")
    c += 1

# Finalize
f.close()
print("----------------------------------------------------------")
print("The new active licenses have been saved to license list.txt")
print("I recommend re-saving the active licenses in a new file for distribution.")
print("----------------------------------------------------------")

print("Press Any Button To Quit")
os.system('pause')
