from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Callable, Union

class BaseFormatHandler(ABC):
    """Базовый абстрактный интерфейс для всех обработчиков форматов."""
    
    @abstractmethod
    def generate(self, target_dir: Path, files: List[Path], content_reader: Callable[[Path], str]) -> Union[str, bytes]:
        pass