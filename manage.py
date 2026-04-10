import os
import subprocess
import sys

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(e.stderr)
        return False

def add_hardbone(domain):
    script_path = "migrate_rules.py"
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found.")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    found = False
    new_lines = []
    for line in lines:
        if "HARDBONES = [" in line:
            found = True
        if found and "]" in line:
            # Insert the new domain before the closing bracket
            new_lines.append(f'    "{domain}",\n')
            found = False
        new_lines.append(line)

    with open(script_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"Successfully added {domain} to HARDBONES.")

def main():
    print("=== ClashRouter Manager ===")
    print("1. Add new Hardbone domain")
    print("2. Run Migration (Update Templates)")
    print("3. Sync to GitHub (Commit & Push)")
    print("4. Exit")
    
    choice = input("Select an option (1-4): ")

    if choice == "1":
        domain = input("Enter the domain to bypass (e.g., example.com): ").strip()
        if domain:
            add_hardbone(domain)
    elif choice == "2":
        print("Running migrate_rules.py...")
        run_command("python3 migrate_rules.py")
    elif choice == "3":
        msg = input("Enter commit message (default: Update rules): ").strip() or "Update rules"
        if run_command("git add .") and run_command(f'git commit -m "{msg}"') and run_command("git push"):
            print("Successfully synced to GitHub.")
    elif choice == "4":
        sys.exit()
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    while True:
        main()
        print("\n")
