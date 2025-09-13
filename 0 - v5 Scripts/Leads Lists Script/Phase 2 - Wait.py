# Wait for the user to confirm that the Keepa source file has been pasted into the directory
user_input = input("When Keepa source file is pasted into the directory, type yes: ")

# Check if the user's input is 'yes' (case-insensitive)
if user_input.strip().lower() == "yes":
    print("Confirmation received. Script complete.")