import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLineEdit, QTextEdit, QPushButton, QLabel)
import re

class ScriptGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Script Code Generator")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # 1. Variable Inputs
        variables_group_layout = QGridLayout()
        variables_group_layout.addWidget(QLabel("eqp_id:"), 0, 0)
        self.eqp_id_input = QLineEdit()
        self.eqp_id_input.setText("test324") # Default value
        variables_group_layout.addWidget(self.eqp_id_input, 0, 1)

        variables_group_layout.addWidget(QLabel("lot_id:"), 1, 0)
        self.lot_id_input = QLineEdit()
        self.lot_id_input.setText("test763.1") # Default value
        variables_group_layout.addWidget(self.lot_id_input, 1, 1)

        variables_group_layout.addWidget(QLabel("step_seq:"), 2, 0)
        self.step_seq_input = QLineEdit()
        self.step_seq_input.setText("test125120") # Default value
        variables_group_layout.addWidget(self.step_seq_input, 2, 1)

        variables_group_layout.addWidget(QLabel("wafer_id (comma-separated):"), 3, 0)
        self.wafer_id_input = QLineEdit()
        self.wafer_id_input.setText("01,02") # Default value
        variables_group_layout.addWidget(self.wafer_id_input, 3, 1)

        main_layout.addLayout(variables_group_layout)

        # 2. Script Input
        main_layout.addWidget(QLabel("Script:"))
        self.script_input = QTextEdit()
        # Default script value based on example 2
        self.script_input.setPlainText(
            "wf_start = [mars_time_robot(LOADPORT)(ATM)(START_TIME)][0]\n"
            "wf_end = [mars_time_robot(ATM)(LOADPORT)(END_TIME)][0]\n"
            "[space_virtual_model_result] = (wf_end - wf_start).total_seconds()"
        )
        main_layout.addWidget(self.script_input)

        # Generate Button
        self.generate_button = QPushButton("Generate Code")
        self.generate_button.clicked.connect(self.generate_code)
        main_layout.addWidget(self.generate_button)

        # 3. Generated Code Output
        main_layout.addWidget(QLabel("Generated Python Code:"))
        self.code_output = QTextEdit()
        self.code_output.setReadOnly(True)
        main_layout.addWidget(self.code_output)

    def generate_code(self):
        eqp_id = self.eqp_id_input.text()
        lot_id = self.lot_id_input.text()
        step_seq = self.step_seq_input.text()
        wafer_id_str = self.wafer_id_input.text()
        wafer_ids = [w.strip() for w in wafer_id_str.split(',') if w.strip()]

        script_lines = self.script_input.toPlainText().strip().split('\n')

        parsed_script = []
        result_var_name = None

        # Regex to find function calls like func(ARG1)(ARG2)...
        # It captures the function name and then all subsequent arguments in parentheses
        func_call_pattern = re.compile(r'(\w+)(\(\w+\))+')

        for line in script_lines:
            line = line.strip()
            if not line or line.startswith('#'): # Skip empty lines or comments
                continue

            if '=' in line:
                left, right = line.split('=', 1)
                left = left.strip()
                right = right.strip()

                # [0]이 끝에 붙어있으면 미리 제거 (함수 호출/일반식 모두 적용)
                if right.endswith('[0]'):
                    right = right[:-3].strip()
                # 대괄호로 감싸져 있으면 대괄호 제거
                if right.startswith('[') and right.endswith(']'):
                    right = right[1:-1].strip()

                is_result_assignment = False
                if left.startswith('[') and left.endswith(']'):
                    var_name = left[1:-1].strip()
                    is_result_assignment = True
                    if result_var_name is None:
                        result_var_name = var_name
                    elif result_var_name != var_name:
                        # Handle case where multiple result variables are defined (not in example, but good to consider)
                        # For this specific request, we assume only one result variable format [var]
                        pass # Or raise an error/warning

                else:
                    var_name = left

                # Parse the right side
                func_match = func_call_pattern.match(right)
                if func_match:
                    # It's a function call like func(ARG1)(ARG2)...[0]
                    func_name = func_match.group(1)
                    # Extract arguments from all subsequent (\w+) groups
                    args_str = func_match.group(2) # This gets the first (\w+) group
                    # Find all arguments in parentheses
                    args = re.findall(r'\((\w+)\)', right)

                    parsed_script.append({
                        'type': 'assignment',
                        'left': var_name,
                        'is_result': is_result_assignment,
                        'right_type': 'function_call',
                        'func_name': func_name,
                        'func_args': args
                    })
                else:
                    # It's likely an expression like (var1 - var2).method()
                     # Remove potential [0] at the end if it exists, as it's handled by the left side [var][i]
                    if right.endswith('[0]'):
                         right = right[:-3].strip()

                    parsed_script.append({
                        'type': 'assignment',
                        'left': var_name,
                        'is_result': is_result_assignment,
                        'right_type': 'expression',
                        'expression': right
                    })
            # Add other line types if needed in the future (e.g., simple variable declarations without assignment)
            # else:
            #     # Handle lines that are not assignments if necessary
            #     pass

        generated_code_lines = []

        if not wafer_ids:
            self.code_output.setPlainText("Error: wafer_id list is empty.")
            return

        if result_var_name:
             # Initialize the result list
            generated_code_lines.append(f"{result_var_name} = [None] * {len(wafer_ids)}")
            generated_code_lines.append("") # Add a blank line for readability

        generated_code_lines.append(f"wafer_ids = {wafer_ids}") # Include the wafer_ids list in the output
        generated_code_lines.append(f"eqp_id = '{eqp_id}'")
        generated_code_lines.append(f"lot_id = '{lot_id}'")
        generated_code_lines.append(f"step_seq = '{step_seq}'")
        generated_code_lines.append("") # Add a blank line

        # Add a placeholder function definition for mars_time_robot and mars_time_hw
        # This is just so the generated code can be run without errors for demonstration
        generated_code_lines.append("##this is a code generated by a script generator app")

        generated_code_lines.append("for i in range(len(wafer_ids)):")
        generated_code_lines.append(f"    current_wafer_id = wafer_ids[i]") # Define current_wafer_id for clarity

        for item in parsed_script:
            if item['type'] == 'assignment':
                left_side = item['left']
                right_side = ""

                if item['right_type'] == 'function_call':
                    func_name = item['func_name']
                    func_args = item['func_args']
                    # step_seq, eqp_id, lot_id, current_wafer_id + 나머지 인자
                    args_list = ["step_seq", "eqp_id", "lot_id", "current_wafer_id"] + [f"'{arg}'" for arg in func_args]
                    right_side = f"{func_name}({', '.join(args_list)})"
                elif item['right_type'] == 'expression':
                    right_side = item['expression']

                # Construct the left side for the generated code
                if item['is_result']:
                    left_side = f"{result_var_name}[i]"

                generated_code_lines.append(f"    {left_side} = {right_side}")

                # Add print statement if it's the result assignment
                if item['is_result']:
                    generated_code_lines.append(f"    print(f\"Result for wafer {{current_wafer_id}}: {{{left_side}}}\")") # Use f-string for print
        generated_code_lines.append("") # Add a blank line after the loop

        if result_var_name:
             generated_code_lines.append(f"print(\"Final results list:\", {result_var_name})")


        self.code_output.setPlainText('\n'.join(generated_code_lines))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScriptGeneratorApp()
    window.show()
    sys.exit(app.exec())