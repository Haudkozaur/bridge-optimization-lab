from dataclasses import dataclass
from typing import Literal


@dataclass
class FloatRange:
    mode: Literal["fixed", "random"]
    min: float
    max: float | None = None

    def __post_init__(self) -> None:
        if self.mode == "fixed":
            self.max = self.min

        elif self.mode == "random":
            if self.max is None:
                raise ValueError("FloatRange in 'random' mode requires min and max")

            if self.min > self.max:
                raise ValueError("FloatRange: min cannot be greater than max")

        else:
            raise ValueError(f"Unsupported FloatRange mode: {self.mode}")

    def validate(self, name: str) -> None:
        if self.min > self.max:
            raise ValueError(f"{name}: min cannot be greater than max")


@dataclass
class IntRange:
    mode: Literal["fixed", "random"]
    min: int
    max: int | None = None

    def __post_init__(self) -> None:
        if self.mode == "fixed":
            self.max = self.min

        elif self.mode == "random":
            if self.max is None:
                raise ValueError("IntRange in 'random' mode requires min and max")

            if self.min > self.max:
                raise ValueError("IntRange: min cannot be greater than max")

        else:
            raise ValueError(f"Unsupported IntRange mode: {self.mode}")

    def validate(self, name: str) -> None:
        if self.min > self.max:
            raise ValueError(f"{name}: min cannot be greater than max")