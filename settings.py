import os
from pathlib import Path
from typing import Any, List, Union
from fastapi import Depends
from utils import get_kb_root
from logger import get_logger

logger = get_logger(__name__)


def init_kbs(kb_root: str = Depends(get_kb_root)):
    # create kb root if not exists
    if not os.path.exists(kb_root):
        logger.info(f"Creating KB root: {kb_root}")
        os.makedirs(kb_root, mode=0o777, exist_ok=False)


# def load_settings(root_path: str, kb_root: str = get_kb_root()):
#     load_dotenv(os.path.join(kb_root, root_path, ".env"))
#     config_path = os.getenv(
#         "GRAPHRAG_CONFIG", os.path.join(kb_root, root_path, "settings.yaml")
#     )
#     if os.path.exists(config_path):
#         with open(config_path, "r") as config_file:
#             config = yaml.safe_load(config_file)
#     else:
#         config = {}
#     settings = {
#         "llm_model": os.getenv("LLM_MODEL", config.get("llm", {}).get("model")),
#         "embedding_model": os.getenv(
#             "EMBEDDINGS_MODEL", config.get("embeddings", {}).get("llm", {}).get("model")
#         ),
#         "community_level": int(os.getenv("COMMUNITY_LEVEL", 2)),
#         "token_limit": int(os.getenv("TOKEN_LIMIT", 4096)),
#         "api_key": os.getenv("GRAPHRAG_API_KEY", config.get("llm", {}).get("api_key")),
#         "api_base": os.getenv("LLM_API_BASE", config.get("llm", {}).get("api_base")),
#         "embeddings_api_key": os.getenv(
#             "EMBEDDINGS_API_KEY",
#             config.get("embeddings", {}).get("llm", {}).get("api_key"),
#         ),
#         "embeddings_api_base": os.getenv(
#             "EMBEDDINGS_API_BASE",
#             config.get("embeddings", {}).get("llm", {}).get("api_base"),
#         ),
#         "api_type": os.getenv("API_TYPE", config.get("api_type", "openai")),
#     }
#     return settings


def update_env_file(param: str, new_value: Any, env_file: str):
    # check if env_file exists
    if not os.path.exists(env_file):
        raise FileNotFoundError(f"Environment file {env_file} not found")
    # 读取现有的环境变量
    env_vars = {}
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    # 更新或添加新的环境变量
    env_vars[param] = str(new_value)
    # 写回文件
    with open(env_file, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")


def update_yaml_config(
    param_value_pairs: List[tuple[str, Any]],
    yaml_file: Union[str, Path],
) -> bool:
    try:
        yaml_path = Path(yaml_file)
        print(yaml_path)
        # 使用 RoundTripLoader 来保持原有格式
        from ruamel.yaml import YAML

        yaml = YAML()
        yaml.preserve_quotes = True  # 保持引号状态
        yaml.indent(mapping=2, sequence=4, offset=2)
        # 读取现有配置
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                config = yaml.load(f)
                if config is None:
                    config = {}
        else:
            config = {}
        # 批量更新配置
        for param_path, new_value in param_value_pairs:
            keys = param_path.split(".")
            current = config
            # 遍历到倒数第二层
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                elif not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]
            # 设置新值，保持原有的格式特征
            current[keys[-1]] = new_value
        # 保存更新后的配置
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)
        return True
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        return False
