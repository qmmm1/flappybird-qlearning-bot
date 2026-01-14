import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import sys
import threading


class FlappyBirdApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flappy Bird AI 训练控制台")
        self.root.geometry("600x500")

        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')

        # 创建主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标题
        title_label = ttk.Label(main_frame, text="Flappy Bird AI 训练控制台",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # 功能选择区域
        ttk.Label(main_frame, text="选择功能:").grid(row=1, column=0, sticky=tk.W, pady=5)

        self.selected_function = tk.StringVar(value="train_with_display")
        functions = [
            ("训练并显示 (推荐)", "train_with_display"),
            ("快速训练 (无显示)", "learn"),
            ("训练并绘图", "learn_draw"),
            ("播放游戏 (AI控制)", "flappy"),
            ("初始化Q值", "initialize_qvalues")
        ]

        for i, (text, value) in enumerate(functions):
            ttk.Radiobutton(main_frame, text=text, variable=self.selected_function,
                            value=value).grid(row=i + 2, column=0, sticky=tk.W, pady=2)

        # 参数设置区域
        params_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="10")
        params_frame.grid(row=2, column=1, rowspan=5, padx=(20, 0), sticky=(tk.W, tk.E, tk.N, tk.S))

        # 迭代次数
        ttk.Label(params_frame, text="迭代次数:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.iter_var = tk.StringVar(value="1000")
        self.iter_entry = ttk.Entry(params_frame, textvariable=self.iter_var, width=15)
        self.iter_entry.grid(row=0, column=1, padx=(10, 0), pady=5)

        # 显示频率
        ttk.Label(params_frame, text="显示频率:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.display_freq_var = tk.StringVar(value="10")
        self.display_freq_entry = ttk.Entry(params_frame, textvariable=self.display_freq_var, width=15)
        self.display_freq_entry.grid(row=1, column=1, padx=(10, 0), pady=5)

        # FPS设置
        ttk.Label(params_frame, text="FPS:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.fps_var = tk.StringVar(value="60")
        self.fps_entry = ttk.Entry(params_frame, textvariable=self.fps_var, width=15)
        self.fps_entry.grid(row=2, column=1, padx=(10, 0), pady=5)

        # 复选框
        self.verbose_var = tk.BooleanVar(value=True)
        self.verbose_check = ttk.Checkbutton(params_frame, text="详细输出", variable=self.verbose_var)
        self.verbose_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)

        self.dump_hitmasks_var = tk.BooleanVar(value=False)
        self.dump_hitmasks_check = ttk.Checkbutton(params_frame, text="导出碰撞掩码",
                                                   variable=self.dump_hitmasks_var)
        self.dump_hitmasks_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        # 输出区域
        output_frame = ttk.LabelFrame(main_frame, text="控制台输出", padding="10")
        output_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0), sticky=(tk.W, tk.E, tk.N, tk.S))

        self.output_text = tk.Text(output_frame, height=10, width=70, wrap=tk.WORD)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.output_text.config(yscrollcommand=scrollbar.set)

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(15, 0))

        self.run_button = ttk.Button(button_frame, text="运行", command=self.run_function)
        self.run_button.grid(row=0, column=0, padx=(0, 10))

        ttk.Button(button_frame, text="清除输出", command=self.clear_output).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="退出", command=self.root.quit).grid(row=0, column=2, padx=(10, 0))

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        # 绑定事件
        self.selected_function.trace('w', self.update_ui)
        self.update_ui()

        # 进程跟踪
        self.process = None

    def update_ui(self, *args):
        """根据选择的功能更新UI"""
        func = self.selected_function.get()

        # 启用/禁用相关控件
        if func == "train_with_display":
            self.iter_entry.config(state="normal")
            self.display_freq_entry.config(state="normal")
            self.fps_entry.config(state="normal")
            self.verbose_check.config(state="normal")
            self.dump_hitmasks_check.config(state="disabled")
        elif func == "learn":
            self.iter_entry.config(state="normal")
            self.display_freq_entry.config(state="disabled")
            self.fps_entry.config(state="disabled")
            self.verbose_check.config(state="normal")
            self.dump_hitmasks_check.config(state="disabled")
        elif func == "learn_draw":
            self.iter_entry.config(state="normal")
            self.display_freq_entry.config(state="disabled")
            self.fps_entry.config(state="disabled")
            self.verbose_check.config(state="normal")
            self.dump_hitmasks_check.config(state="disabled")
        elif func == "flappy":
            self.iter_entry.config(state="disabled")
            self.display_freq_entry.config(state="disabled")
            self.fps_entry.config(state="normal")
            self.verbose_check.config(state="disabled")
            self.dump_hitmasks_check.config(state="normal")
        elif func == "initialize_qvalues":
            self.iter_entry.config(state="disabled")
            self.display_freq_entry.config(state="disabled")
            self.fps_entry.config(state="disabled")
            self.verbose_check.config(state="disabled")
            self.dump_hitmasks_check.config(state="disabled")

    def clear_output(self):
        """清除输出区域"""
        self.output_text.delete(1.0, tk.END)

    def append_output(self, text):
        """向输出区域添加文本"""
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def run_function(self):
        """运行选择的功能"""
        func = self.selected_function.get()

        # 构建命令
        cmd = ["python"]

        if func == "train_with_display":
            cmd.append("train_with_display.py")
            cmd.extend(["--iter", self.iter_var.get()])
            cmd.extend(["--display_freq", self.display_freq_var.get()])
            if self.verbose_var.get():
                cmd.append("--verbose")

        elif func == "learn":
            cmd.append("learn.py")
            cmd.extend(["--iter", self.iter_var.get()])
            if self.verbose_var.get():
                cmd.append("--verbose")

        elif func == "learn_draw":
            cmd.append("learn_draw.py")
            cmd.extend(["--iter", self.iter_var.get()])
            if self.verbose_var.get():
                cmd.append("--verbose")

        elif func == "flappy":
            cmd.append("flappy.py")
            cmd.extend(["--fps", self.fps_var.get()])
            if self.dump_hitmasks_var.get():
                cmd.append("--dump_hitmasks")

        elif func == "initialize_qvalues":
            cmd.append("initialize_qvalues.py")

        # 在新线程中运行命令
        self.run_button.config(state="disabled")
        self.status_var.set("运行中...")

        thread = threading.Thread(target=self.execute_command, args=(cmd, func))
        thread.daemon = True
        thread.start()

    def execute_command(self, cmd, func_name):
        """执行命令并捕获输出"""
        try:
            self.append_output(f"正在运行: {' '.join(cmd)}\n")
            self.append_output("-" * 50 + "\n")

            # 运行子进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # 实时读取输出
            for line in self.process.stdout:
                self.append_output(line)

            # 等待进程结束
            return_code = self.process.wait()

            if return_code == 0:
                self.append_output(f"\n{func_name} 执行成功!\n")
                self.status_var.set("执行完成")
            else:
                self.append_output(f"\n{func_name} 执行失败，返回码: {return_code}\n")
                self.status_var.set("执行失败")

        except Exception as e:
            self.append_output(f"错误: {str(e)}\n")
            self.status_var.set("发生错误")
        finally:
            self.process = None
            self.root.after(0, self.enable_run_button)

    def enable_run_button(self):
        """重新启用运行按钮"""
        self.run_button.config(state="normal")

    def on_closing(self):
        """窗口关闭时的处理"""
        if self.process and self.process.poll() is None:
            if messagebox.askokcancel("退出", "有程序正在运行，确定要退出吗？"):
                self.process.terminate()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = FlappyBirdApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()