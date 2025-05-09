#!/usr/bin/env python
print("Hello, world!")
print("Running simple test...")

# Test if we can create a file
with open("test_output.txt", "w") as f:
    f.write("This is a test file.")

print("Test completed successfully.") 