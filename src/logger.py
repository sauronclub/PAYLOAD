# -*- coding: utf-8 -*-
# 导入Python内置的logging模块，用于实现日志功能
import logging


def setup_logger(name: str = "名称为空，请设置日志器名称", level: int = logging.INFO) -> logging.Logger:
    """
    初始化并配置一个标准化的控制台日志器（Logger）
    核心特性：防重复添加处理器、统一日志格式、支持自定义日志器名称和级别
    
    :param name: 日志器名称，用于区分不同模块的日志，默认值"名称为空，请设置日志器名称"
    :param level: 日志输出级别，默认logging.INFO（仅输出INFO及以上级别日志）
    :return: 配置完成的logging.Logger实例，可直接用于输出日志
    """
    # 1. 创建/获取指定名称的日志器实例（logging模块单例特性：同名返回同一个实例）
    # 作用：通过名称隔离不同模块的日志，避免日志混乱
    logger = logging.getLogger(name)
    
    # 2. 设置日志器的全局级别
    # 作用：只有级别≥该值的日志会被处理（如INFO级别会过滤掉DEBUG日志）
    # 注意：日志器级别是"总开关"，处理器级别是"细分开关"
    logger.setLevel(level)

    # 3. 核心防重复逻辑：检查日志器是否已绑定处理器
    # 作用：避免多次调用该函数时重复添加控制台处理器，导致日志重复打印
    if logger.handlers:
        # 已有处理器则直接返回已配置好的日志器，无需重复配置
        return logger

    # 4. 创建控制台处理器（StreamHandler默认输出到标准输出/控制台）
    # 作用：定义日志的输出目标（此处为控制台，也可改为文件/网络等）
    console_handler = logging.StreamHandler()
    
    # 5. 设置控制台处理器的日志级别
    # 作用：精细化控制该处理器的输出门槛（此处与日志器级别保持一致）
    console_handler.setLevel(level)

    # 6. 创建日志格式器，定义日志的输出格式
    # 格式说明：
    # %(asctime)s: 日志产生的时间戳（如2026-03-06 16:00:00）
    # %(levelname)s: 日志级别名称（如INFO/ERROR）
    # %(message)s: 日志的具体内容
    # 作用：统一日志格式，便于阅读和排查问题
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    
    # 7. 将格式器绑定到控制台处理器
    # 作用：让该处理器输出的日志按照指定格式展示
    console_handler.setFormatter(formatter)

    # 8. 将配置好的控制台处理器添加到日志器
    # 作用：完成日志器与处理器的绑定，日志器的日志会通过该处理器输出
    logger.addHandler(console_handler)

    # 9. 返回配置完成的日志器实例，供外部调用
    return logger