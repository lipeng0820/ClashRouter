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
    print("=== ClashRouter 规则管理器 ===")
    print("1. 添加新的“硬骨头”域名 (直连白名单)")
    print("2. 执行同步 (更新所有分流配置文件)")
    print("3. 同步到 GitHub (自动提交并推送)")
    print("4. 退出")
    
    choice = input("请选择操作 (1-4): ")

    if choice == "1":
        domain = input("请输入要放行的域名 (例如: example.com): ").strip()
        if domain:
            add_hardbone(domain)
    elif choice == "2":
        print("正在运行 migrate_rules.py 更新模版...")
        run_command("python3 migrate_rules.py")
    elif choice == "3":
        msg = input("请输入提交信息 (直接回车默认为: 更新分流规则): ").strip() or "更新分流规则"
        if run_command("git add .") and run_command(f'git commit -m "{msg}"') and run_command("git push"):
            print("🎉 已成功同步到 GitHub！")
    elif choice == "4":
        sys.exit()
    else:
        print("无效选择，请重试。")

if __name__ == "__main__":
    while True:
        main()
        print("\n")
