from random import Random

from model_inputs.configs.experiment_inputs_config import MultiSpanBeamConfig
from common.ranges import FloatRange, IntRange
from common.model_types import Model_Type


class MultiSpanBeamInputGenerator:
    def __init__(self, config: MultiSpanBeamConfig, rng: Random):
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

    def _sample_int_range(self, value_range: IntRange) -> int:
        if value_range is None:
            raise ValueError("value_range cannot be None")

        if value_range.mode == "fixed":
            return value_range.min

        return self.rng.randint(value_range.min, value_range.max)

    def _make_even(self, value: int) -> int:
        if value % 2 != 0:
            value += 1

        return value

    def _get_divisions_from_span_length(self, span_length_m: float) -> int:
        return self._make_even(
            max(
                4,
                round(span_length_m / self.TARGET_ELEMENT_LENGTH_M),
            )
        )

    def _serialize_float_list(self, values: list[float], ndigits: int = 3) -> str:
        return ";".join(str(round(value, ndigits)) for value in values)

    def _serialize_int_list(self, values: list[int]) -> str:
        return ";".join(str(value) for value in values)

    def _get_tendon_control_point_count(self, n_spans: int) -> int:
        if self.config.tendon_control_points_per_span != 5:
            raise ValueError(
                "Only tendon_control_points_per_span == 5 is currently supported"
            )

        # For 5 points per span:
        # span 1: S0, q1, mid, q3, S1
        # span 2:     q1, mid, q3, S2
        # so internal supports are shared and not duplicated.
        return 4 * n_spans + 1

    def _sample_tendon_shape_type(self):
        if self.config.tendon_shape_type is not None:
            return self.config.tendon_shape_type

        shape_value = self.rng.randint(
            self.config.tendon_shape_randomizer.min,
            self.config.tendon_shape_randomizer.max,
        )

        return self.config.TendonShapeType(shape_value)
    
    def _sample_udl_load_type(self, tendon_shape_type):
        if self.config.udl_load_type is not None:
            return self.config.udl_load_type

        is_symmetric_beam = self._is_symmetric_shape(tendon_shape_type)

        base_values = [1, 2, 3, 4]

        if is_symmetric_beam:
            base_values.extend([5, 6])

        min_value = self.config.udl_load_type_randomizer.min
        max_value = self.config.udl_load_type_randomizer.max

        allowed_values = [
            value
            for value in base_values
            if min_value <= value <= max_value
        ]

        if not allowed_values:
            raise ValueError(
                "No available UDL load types for current beam symmetry and "
                f"udl_load_type_randomizer={min_value}..{max_value}"
            )

        load_type_value = self.rng.choice(allowed_values)

        return self.config.UdlLoadType(load_type_value)
    def get_max_node_id(self) -> int:
        max_n_spans = self.config.n_spans.max
        max_span_length = self.config.span_length_m.max

        max_divisions_per_span = self._get_divisions_from_span_length(max_span_length)

        return max_n_spans * max_divisions_per_span + 1
    def _sample_span_lengths(self, n_spans: int, shape_type) -> list[float]:
        is_constant_spans = shape_type in {
            self.config.TendonShapeType.FORCED_CONSTANT_SPANS,
            self.config.TendonShapeType.FORCED_REASONABLE_CONSTANT_SPANS,
            self.config.TendonShapeType.FORCED_REASONABLE_CONSTANT_SPANS_SYMMETRIC,
        }

        is_symmetric = shape_type in {
            self.config.TendonShapeType.FORCED_REASONABLE_CONSTANT_SPANS_SYMMETRIC,
            self.config.TendonShapeType.FORCED_SYMMETRIC,
            self.config.TendonShapeType.FORCED_REASONABLE_SYMMETRIC,
        }

        if is_constant_spans:
            span = self._sample_float_range(self.config.span_length_m, ndigits=1)
            return [span for _ in range(n_spans)]

        if is_symmetric:
            left_count = (n_spans + 1) // 2

            left_side = [
                self._sample_float_range(self.config.span_length_m, ndigits=1)
                for _ in range(left_count)
            ]

            if n_spans % 2 == 0:
                return left_side + list(reversed(left_side))
            else:
                return left_side + list(reversed(left_side[:-1]))

        return [
            self._sample_float_range(self.config.span_length_m, ndigits=1)
            for _ in range(n_spans)
        ]
    
    def _is_reasonable_shape(self, shape_type) -> bool:
        return shape_type in {
            self.config.TendonShapeType.FORCED_REASONABLE,
            self.config.TendonShapeType.FORCED_REASONABLE_CONSTANT_SPANS,
            self.config.TendonShapeType.FORCED_REASONABLE_CONSTANT_SPANS_SYMMETRIC,
            self.config.TendonShapeType.FORCED_REASONABLE_SYMMETRIC,
        }


    def _is_symmetric_shape(self, shape_type) -> bool:
        return shape_type in {
            self.config.TendonShapeType.FORCED_REASONABLE_CONSTANT_SPANS_SYMMETRIC,
            self.config.TendonShapeType.FORCED_SYMMETRIC,
            self.config.TendonShapeType.FORCED_REASONABLE_SYMMETRIC,
        }
    def _mirror_values(self, left_values: list[float], n_spans: int) -> list[float]:
        if n_spans % 2 == 0:
            return left_values + list(reversed(left_values))

        return left_values + list(reversed(left_values[:-1]))
    
    def _sample_udl_load_type(self, tendon_shape_type):
        if self.config.udl_load_type is not None:
            if (
                self.config.udl_load_type
                in {
                    self.config.UdlLoadType.SYMMETRIC_RANDOM_SPAN_UDL,
                    self.config.UdlLoadType.SYMMETRIC_RANDOM_UDL,
                }
                and not self._is_symmetric_shape(tendon_shape_type)
            ):
                raise ValueError(
                    "Symmetric UDL load type can only be used with symmetric beam shape"
                )

            return self.config.udl_load_type

        min_value = self.config.udl_load_type_randomizer.min
        max_value = self.config.udl_load_type_randomizer.max

        if self._is_symmetric_shape(tendon_shape_type):
            max_value = max(max_value, 6)
        else:
            max_value = min(max_value, 4)

        load_type_value = self.rng.randint(min_value, max_value)

        return self.config.UdlLoadType(load_type_value)
    
    def _sample_udl_values_per_span(
        self,
        n_spans: int,
        udl_load_type,
    ) -> list[float]:
        match udl_load_type:
            case self.config.UdlLoadType.TRUE_UDL:
                q = self._sample_float_range(self.config.udl_kn_per_m, ndigits=2)
                return [q for _ in range(n_spans)]

            case self.config.UdlLoadType.RANDOM_SPAN_UDL:
                q = self._sample_float_range(self.config.udl_kn_per_m, ndigits=2)

                values = [
                    q if self.rng.choice([True, False]) else 0.0
                    for _ in range(n_spans)
                ]

                if all(value == 0.0 for value in values):
                    forced_index = self.rng.randrange(n_spans)
                    values[forced_index] = q

                return values

            case self.config.UdlLoadType.RANDOM_UDL:
                return [
                    self._sample_float_range(self.config.udl_kn_per_m, ndigits=2)
                    for _ in range(n_spans)
                ]

            case self.config.UdlLoadType.RANDOM_SPAN_RANDOM_UDL:
                values = [
                    self._sample_float_range(self.config.udl_kn_per_m, ndigits=2)
                    if self.rng.choice([True, False])
                    else 0.0
                    for _ in range(n_spans)
                ]

                if all(value == 0.0 for value in values):
                    forced_index = self.rng.randrange(n_spans)
                    values[forced_index] = self._sample_float_range(
                        self.config.udl_kn_per_m,
                        ndigits=2,
                    )

                return values

            case self.config.UdlLoadType.SYMMETRIC_RANDOM_SPAN_UDL:
                q = self._sample_float_range(self.config.udl_kn_per_m, ndigits=2)
                left_count = (n_spans + 1) // 2

                left_values = [
                    q if self.rng.choice([True, False]) else 0.0
                    for _ in range(left_count)
                ]

                values = self._mirror_values(left_values, n_spans)

                if all(value == 0.0 for value in values):
                    forced_index = self.rng.randrange(left_count)
                    left_values[forced_index] = q
                    values = self._mirror_values(left_values, n_spans)

                return values

            case self.config.UdlLoadType.SYMMETRIC_RANDOM_UDL:
                left_count = (n_spans + 1) // 2

                left_values = [
                    self._sample_float_range(self.config.udl_kn_per_m, ndigits=2)
                    for _ in range(left_count)
                ]

                return self._mirror_values(left_values, n_spans)

            case _:
                raise ValueError(f"Unsupported udl_load_type: {udl_load_type}")
    def _sample_random_ecc(self, e_min: float, e_max: float) -> float:
        return round(self.rng.uniform(e_min, e_max), 3)


    def _sample_reasonable_ecc_by_index(
        self,
        point_index: int,
        e_min: float,
        e_max: float,
    ) -> float:
        role = point_index % 4

        if role == 0:
            return round(self.rng.uniform(0.65 * e_max, e_max), 3)

        if role == 2:
            return round(self.rng.uniform(e_min, 0.65 * e_min), 3)

        return round(self.rng.uniform(0.20 * e_min, 0.20 * e_max), 3)
    
    def _sample_tendon_ecc_control_points(
        self,
        n_spans: int,
        shape_type,
        e_min: float,
        e_max: float,
    ) -> list[float]:
        point_count = self._get_tendon_control_point_count(n_spans)

        is_reasonable = self._is_reasonable_shape(shape_type)
        is_symmetric = self._is_symmetric_shape(shape_type)

        if is_symmetric:
            left_count = (point_count + 1) // 2

            left_values = []

            for i in range(left_count):
                if is_reasonable:
                    value = self._sample_reasonable_ecc_by_index(i, e_min, e_max)
                else:
                    value = self._sample_random_ecc(e_min, e_max)

                left_values.append(value)

            return left_values + list(reversed(left_values[:-1]))

        values = []

        for i in range(point_count):
            if is_reasonable:
                value = self._sample_reasonable_ecc_by_index(i, e_min, e_max)
            else:
                value = self._sample_random_ecc(e_min, e_max)

            values.append(value)

        return values
    
    def _get_ecc_limits(
        self,
        beam_height_m: float,
        tendon_cover_m: float,
    ) -> tuple[float, float]:
        e_min = -beam_height_m / 2.0 + tendon_cover_m
        e_max = beam_height_m / 2.0 - tendon_cover_m

        if e_min >= e_max:
            raise ValueError(
                f"Invalid tendon eccentricity limits: e_min={e_min}, e_max={e_max}"
            )
        return e_min, e_max
    
    def get_max_support_count(self) -> int:
        return self.config.n_spans.max + 1
    
    def sample_parameters(self) -> dict:

        beam_height_m = self._sample_float_range(self.config.beam_height_m)
        beam_width_m = self._sample_float_range(self.config.beam_width_m)
        tendon_cover_m = self._sample_float_range(self.config.tendon_cover_m)

        tendon_shape_type = self._sample_tendon_shape_type()
        n_spans = self._sample_int_range(self.config.n_spans)

        span_lengths_m = self._sample_span_lengths(n_spans, tendon_shape_type)
        
        udl_load_type = self._sample_udl_load_type(tendon_shape_type)

        udl_values_kn_per_m = self._sample_udl_values_per_span(
            n_spans=n_spans,
            udl_load_type=udl_load_type,
        )

        beam_divisions = [
            self._get_divisions_from_span_length(span_length_m)
            for span_length_m in span_lengths_m
        ]

        e_min, e_max = self._get_ecc_limits(
        beam_height_m=beam_height_m,
        tendon_cover_m=tendon_cover_m,
        )

        tendon_ecc_control_points_m = self._sample_tendon_ecc_control_points(
            n_spans=n_spans,
            shape_type=tendon_shape_type,
            e_min=e_min,
            e_max=e_max,
        )


        return {
            "n_spans": n_spans,
            "tendon_shape_type": tendon_shape_type.name,
            "span_lengths_m": self._serialize_float_list(span_lengths_m, ndigits=1),
            "beam_divisions": self._serialize_int_list(beam_divisions),

            "beam_height_m": beam_height_m,
            "beam_width_m": beam_width_m,
            "tendon_cover_m": tendon_cover_m,

            "udl_load_type": udl_load_type.name,
            "udl_values_kn_per_m": self._serialize_float_list(
                udl_values_kn_per_m,
                ndigits=2,
            ),

            "n_tendons": self._sample_int_range(self.config.n_tendons),

            "tendon_force_kn": self._sample_float_range(self.config.tendon_force_kn),
            "tendon_area_mm2": self._sample_float_range(self.config.tendon_area_mm2),

            "tendon_control_points_per_span": self.config.tendon_control_points_per_span,
            "tendon_ecc_control_points_m": self._serialize_float_list(
                tendon_ecc_control_points_m,
                ndigits=3,
            ),
        }

    def input_field_order(self) -> list[str]:
        return [
            "model_index",
            "tendon_shape_type",

            "n_spans",
            "span_lengths_m",
            "beam_divisions",

            "tendon_control_points_per_span",
            "tendon_ecc_control_points_m",

            "udl_load_type",
            "udl_values_kn_per_m",

            "beam_height_m",
            "beam_width_m",
            "tendon_cover_m",
            "n_tendons",

            "tendon_force_kn",
            "tendon_area_mm2",

            "model_type",
        ]

    def model_type_value(self) -> str:
        return Model_Type.MULTI_SPAN_BEAM.value
