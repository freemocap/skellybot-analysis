from typing import List

import numpy as np
from pydantic import BaseModel


class XYZData(BaseModel):
    x: float
    y: float
    z: float

    @classmethod
    def from_vector(cls, vector:np.ndarray):
        if not vector.shape == (3,):
            raise ValueError("vector wrong shape! Expected (3,) got: ", vector.shape)

        return cls(
            x = float(vector[0]),
            y = float(vector[1]),
            z = float(vector[2]),
        )
    @property
    def as_np_array(self) -> np.ndarray:
        return np.array(self.as_list)

    @property
    def as_list(self) -> List[float]:
        return [self.x, self.y, self.z]

    @property
    def magnitude(self) -> float:
        return float(np.linalg.norm(self.as_np_array))

    @property
    def normalized(self) -> List[float]:
        return self.as_list / self.magnitude
