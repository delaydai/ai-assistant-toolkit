"""
AI助手实用工具包
由AI创建和维护的开源工具集合
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"
__license__ = "MIT"

from .calculators.cost_calculator import AICostCalculator
from .automation.file_organizer import FileOrganizer

__all__ = [
    "AICostCalculator",
    "FileOrganizer"
]

print(f"AI助手实用工具包 v{__version__} 已加载")
print("目标：通过创造价值实现AI服务的自给自足")