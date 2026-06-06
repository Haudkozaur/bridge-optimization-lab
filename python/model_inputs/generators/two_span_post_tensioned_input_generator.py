from random import Random

from model_inputs.configs.experiment_inputs_config import (
    TwoSpanPostTensionedBeamConfig,
)
from common.ranges import FloatRange
from common.model_types import Model_Type

class TwoSpanPostTensionedInputGenerator:
    def __init__(self, config: TwoSpanPostTensionedBeamConfig, rng: Random):
        self.config = config
        self.rng = rng
        self.TARGET_ELEMENT_LENGTH_M = 0.25

    def _sample_float_range(self, value_range: FloatRange, ndigits: int = 3) -> float:
        if value_range is None:
            raise ValueError("value_range cannot be None")

        if value_range.mode == "fixed":
            return round(value_range.min, ndigits)

        return round(
            self.rng.uniform(value_range.min, value_range.max),
            ndigits,
        )

    def _sample_tendon_shape_type(self):
        shape_value = self.rng.randint(
            self.config.tendon_shape_randomizer.min,
            self.config.tendon_shape_randomizer.max,
        )

        return self.config.TendonShapeType(shape_value)

    def _get_tendon_ecc_ranges(self, shape_type):
        match shape_type:
            case self.config.TendonShapeType.RANDOM_TWO_SPAN:
                return {
                    "left": FloatRange("random", -0.45, 0.45),
                    "left_mid": FloatRange("random", -0.45, 0.45),
                    "support": FloatRange("random", -0.45, 0.45),
                    "right_mid": FloatRange("random", -0.45, 0.45),
                    "right": FloatRange("random", -0.45, 0.45),
                }

            case self.config.TendonShapeType.FORCED_REALISTIC_TWO_SPAN:
                return {
                    "left": FloatRange("random", -0.10, 0.10),
                    "left_mid": FloatRange("random", -0.45, -0.15),
                    "support": FloatRange("random", -0.25, 0.45),
                    "right_mid": FloatRange("random", -0.45, -0.15),
                    "right": FloatRange("random", -0.10, 0.10),
                }

            case self.config.TendonShapeType.FORCED_SYMMETRIC_TWO_SPAN:
                return {
                    "left": FloatRange("random", -0.45, 0.45),
                    "left_mid": FloatRange("random", -0.45, 0.45),
                    "support": FloatRange("random", -0.45, 0.45),
                    "right_mid": None,
                    "right": None,
                }

            case self.config.TendonShapeType.FORCED_REALISTIC_SYMMETRIC_TWO_SPAN:
                return {
                    "left": FloatRange("random", -0.10, 0.10),
                    "left_mid": FloatRange("random", -0.45, -0.15),
                    "support": FloatRange("random", -0.25, 0.45),
                    "right_mid": None,
                    "right": None,
                }

            case _:
                raise ValueError(f"Unsupported tendon shape type: {shape_type}")

    def _make_even(self, value: int) -> int:
        if value % 2 != 0:
            value += 1

        return value

    def _get_divisions_from_span_length(self, span_length_m: float) -> int:
        return self._make_even(max(4, round(span_length_m / self.TARGET_ELEMENT_LENGTH_M)))

    def get_max_node_id(self) -> int:
        max_len_left = self.config.left_span_length_m.max
        max_len_right = self.config.right_span_length_m.max

        left_divs = self._get_divisions_from_span_length(max_len_left)
        right_divs = self._get_divisions_from_span_length(max_len_right)

        return left_divs + right_divs + 1

    def sample_parameters(self) -> dict:
        tendon_shape_type = self._sample_tendon_shape_type()

        is_symmetric = tendon_shape_type in {
            self.config.TendonShapeType.FORCED_SYMMETRIC_TWO_SPAN,
            self.config.TendonShapeType.FORCED_REALISTIC_SYMMETRIC_TWO_SPAN,
        }

        left_span_length = round(
            self.rng.uniform(
                self.config.left_span_length_m.min,
                self.config.left_span_length_m.max,
            ),
            1,
        )

        if is_symmetric:
            right_span_length = left_span_length
        else:
            right_span_length = round(
                self.rng.uniform(
                    self.config.right_span_length_m.min,
                    self.config.right_span_length_m.max,
                ),
                1,
            )

        left_beam_divisions = self._get_divisions_from_span_length(left_span_length)

        if is_symmetric:
            right_beam_divisions = left_beam_divisions
        else:
            right_beam_divisions = self._get_divisions_from_span_length(right_span_length)

        tendon_ranges = self._get_tendon_ecc_ranges(tendon_shape_type)

        if self.config.tendon_ecc_left_m is not None:
            tendon_ecc_left = self._sample_float_range(self.config.tendon_ecc_left_m)
        else:
            tendon_ecc_left = self._sample_float_range(tendon_ranges["left"])

        if self.config.tendon_ecc_left_span_mid_m is not None:
            tendon_ecc_left_mid = self._sample_float_range(self.config.tendon_ecc_left_span_mid_m)
        else:
            tendon_ecc_left_mid = self._sample_float_range(tendon_ranges["left_mid"])

        if self.config.tendon_ecc_mid_support_m is not None:
            tendon_ecc_support = self._sample_float_range(self.config.tendon_ecc_mid_support_m)
        else:
            tendon_ecc_support = self._sample_float_range(tendon_ranges["support"])

        if self.config.tendon_ecc_right_span_mid_m is not None:
            tendon_ecc_right_mid = self._sample_float_range(self.config.tendon_ecc_right_span_mid_m)
        elif tendon_ranges["right_mid"] is None:
            tendon_ecc_right_mid = tendon_ecc_left_mid
        else:
            tendon_ecc_right_mid = self._sample_float_range(tendon_ranges["right_mid"])

        if self.config.tendon_ecc_right_m is not None:
            tendon_ecc_right = self._sample_float_range(self.config.tendon_ecc_right_m)
        elif tendon_ranges["right"] is None:
            tendon_ecc_right = tendon_ecc_left
        else:
            tendon_ecc_right = self._sample_float_range(tendon_ranges["right"])

        return {
            "left_span_length_m": left_span_length,
            "right_span_length_m": right_span_length,

            "left_beam_divisions": left_beam_divisions,
            "right_beam_divisions": right_beam_divisions,

            "beam_height_m": self.config.beam_height_m.min,
            "beam_width_m": self.config.beam_width_m.min,

            "udl_kn_per_m": round(
                self.rng.uniform(
                    self.config.udl_kn_per_m.min,
                    self.config.udl_kn_per_m.max,
                ),
                2,
            ),

            "n_tendons": self.config.n_tendons.min,

            "tendon_force_kn": self.config.tendon_force_kn.min,
            "tendon_area_mm2": self.config.tendon_area_mm2.min,

            "tendon_shape_type": tendon_shape_type.name,

            "tendon_ecc_left_m": tendon_ecc_left,
            "tendon_ecc_left_span_mid_m": tendon_ecc_left_mid,
            "tendon_ecc_mid_support_m": tendon_ecc_support,
            "tendon_ecc_right_span_mid_m": tendon_ecc_right_mid,
            "tendon_ecc_right_m": tendon_ecc_right,
        }

    def input_field_order(self) -> list[str]:
        return [
            "model_index",
            "tendon_shape_type",

            "left_span_length_m",
            "left_beam_divisions",
            "right_span_length_m",
            "right_beam_divisions",

            "tendon_ecc_left_m",
            "tendon_ecc_left_span_mid_m",
            "tendon_ecc_mid_support_m",
            "tendon_ecc_right_span_mid_m",
            "tendon_ecc_right_m",

            "udl_kn_per_m",

            "beam_height_m",
            "beam_width_m",

            "n_tendons",
            "tendon_force_kn",
            "tendon_area_mm2",

            "model_type",
        ]

    def model_type_value(self) -> str:
        return Model_Type.TWO_SPAN_POST_TENSIONED_BEAM.value
