# -*- coding: utf-8 -*-
# @Author: xiaocao
# @Date:   2023-04-26 13:44:13
# @Last Modified by:   xiaocao
# @Last Modified time: 2023-04-27 21:27:20
import pathlib
import yaml


def load_config():
    config_text = pathlib.Path(
        "./src/config.yaml",
    ).read_text(encoding="utf-8")
    config_dict = yaml.safe_load(config_text)
    return config_dict


if __name__ == "__main__":
    print(load_config())
