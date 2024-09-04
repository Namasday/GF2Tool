import time
from pydantic import BaseModel, Field

from rapidocr_openvino import RapidOCR
ocr = RapidOCR(
    min_height=210,
    det_limit_side_len=40,
)


class PositionModel(BaseModel):
    """
    位置模型
    """
    x1: int = Field(None, title="x1")
    y1: int = Field(None, title="y1")
    x2: int = Field(None, title="x2")
    y2: int = Field(None, title="y2")

    def __str__(self):
        return f"({self.x1}, {self.y1}, {self.x2}, {self.y2})"


def timer(func):
    """
    一个装饰器，用于计算并打印函数的执行时间
    """
    def wrapper(*args, **kwargs):
        # 记录开始时间
        start_time = time.time()
        # 调用原函数
        result = func(*args, **kwargs)
        # 记录结束时间
        end_time = time.time()
        # 计算并打印执行时间
        print(f"{func.__name__} executed in {end_time - start_time:.8f} seconds")
        # 返回原函数的返回值
        return result
    return wrapper


def logger(text):
    print(text)

