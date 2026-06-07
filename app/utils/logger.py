import logging
import os
from datetime import datetime

def setup_logger():
    logger = logging.getLogger("ai_data_analysis")
    logger.setLevel(logging.INFO)
    
    log_dir = os.environ.get("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_tool_call(tool_name, input_params, output_result, execution_time):
    logger = logging.getLogger("ai_data_analysis")
    logger.info(f"Tool Call - {tool_name}: input={input_params}, output={output_result}, time={execution_time}ms")

def log_agent_execution(agent_name, task, status, details):
    logger = logging.getLogger("ai_data_analysis")
    logger.info(f"Agent Execution - {agent_name}: task={task}, status={status}, details={details}")