from os import makedirs, path

from typing import Iterable, List

from common import format_float

from .common import (
    Align, Author, BoolValue, Category, Circle, Created, Deprecated, Description, EnumValue, FloatValue, GeneratedBy,
    Height, Keywords, Layer, Name, Polygon, Position, Position3D, Rotation, Rotation3D, UUIDValue, Value, Version,
    Vertex
)
from .helper import indent_entities


class Package3DModel():
    """
    A 3D model in a package.
    """
    def __init__(self, uuid: str, name: Name):
        self.uuid = uuid
        self.name = name

    def __str__(self) -> str:
        return f'(3d_model {self.uuid} {self.name})\n'

    def __eq__(self, other):  # type: ignore
        return self.uuid == other.uuid and self.name == other.name

    def __lt__(self, other):  # type: ignore
        if self.uuid == other.uuid:
            return self.name < other.name
        return self.uuid < other.uuid


class Footprint3DModel():
    """
    A 3D model reference in a footprint.
    """
    def __init__(self, uuid: str):
        self.uuid = uuid

    def __str__(self) -> str:
        return f'(3d_model {self.uuid})\n'

    def __eq__(self, other):  # type: ignore
        return self.uuid == other.uuid

    def __lt__(self, other):  # type: ignore
        return self.uuid < other.uuid


class AssemblyType(EnumValue):
    NONE = 'none'
    THT = 'tht'
    SMT = 'smt'
    MIXED = 'mixed'
    OTHER = 'other'
    AUTO = 'auto'

    def get_name(self) -> str:
        return 'assembly_type'


class PackagePad():
    def __init__(self, uuid: str, name: Name):
        self.uuid = uuid
        self.name = name

    def __str__(self) -> str:
        return '(pad {} {})'.format(self.uuid, self.name)


class StrokeWidth(FloatValue):
    def __init__(self, stroke_width: float):
        super().__init__('stroke_width', stroke_width)


class LetterSpacing(EnumValue):
    AUTO = 'auto'

    def get_name(self) -> str:
        return 'letter_spacing'


class LineSpacing(EnumValue):
    AUTO = 'auto'

    def get_name(self) -> str:
        return 'line_spacing'


class AutoRotate(BoolValue):
    def __init__(self, auto_rotate: bool):
        super().__init__('auto_rotate', auto_rotate)


class Mirror(BoolValue):
    def __init__(self, mirror: bool):
        super().__init__('mirror', mirror)


class StrokeText():
    def __init__(self, uuid: str, layer: Layer, height: Height,
                 stroke_width: StrokeWidth, letter_spacing: LetterSpacing,
                 line_spacing: LineSpacing, align: Align, position: Position,
                 rotation: Rotation, auto_rotate: AutoRotate, mirror: Mirror,
                 value: Value):
        self.uuid = uuid
        self.layer = layer
        self.height = height
        self.stroke_width = stroke_width
        self.letter_spacing = letter_spacing
        self.line_spacing = line_spacing
        self.align = align
        self.position = position
        self.rotation = rotation
        self.auto_rotate = auto_rotate
        self.mirror = mirror
        self.value = value

    def __str__(self) -> str:
        ret = '(stroke_text {} {}\n'.format(self.uuid, self.layer) +\
            ' {} {} {} {}\n'.format(self.height, self.stroke_width, self.letter_spacing, self.line_spacing) +\
            ' {} {} {}\n'.format(self.align, self.position, self.rotation) +\
            ' {} {} {}\n)'.format(self.auto_rotate, self.mirror, self.value)
        return ret


class ComponentSide(EnumValue):
    TOP = 'top'
    BOTTOM = 'bottom'

    def get_name(self) -> str:
        return 'side'


class Shape(EnumValue):
    ROUNDED_RECT = 'roundrect'
    ROUNDED_OCTAGON = 'octagon'
    CUSTOM = 'custom'

    def get_name(self) -> str:
        return 'shape'


class ShapeRadius(FloatValue):
    def __init__(self, radius_normalized: float):
        super().__init__('radius', radius_normalized)


class Size():
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def __str__(self) -> str:
        return '(size {} {})'.format(format_float(self.width), format_float(self.height))


class StopMaskConfig(EnumValue):
    AUTO = 'auto'
    OFF = 'off'

    def get_name(self) -> str:
        return 'stop_mask'


class SolderPasteConfig(EnumValue):
    AUTO = 'auto'
    OFF = 'off'

    def get_name(self) -> str:
        return 'solder_paste'


class CopperClearance(FloatValue):
    def __init__(self, clearance: float):
        super().__init__('clearance', clearance)


class PackagePadUuid(UUIDValue):
    def __init__(self, package_pad: str):
        super().__init__('package_pad', package_pad)


class PadFunction(EnumValue):
    UNSPECIFIED = 'unspecified'
    STANDARD_PAD = 'standard'
    PRESSFIT_PAD = 'pressfit'
    THERMAL_PAD = 'thermal'
    BGA_PAD = 'bga'
    EDGE_CONNECTOR_PAD = 'edge_connector'
    TEST_PAD = 'test'
    LOCAL_FIDUCIAL = 'local_fiducial'
    GLOBAL_FIDUCIAL = 'global_fiducial'

    def get_name(self) -> str:
        return 'function'


class DrillDiameter(FloatValue):
    def __init__(self, diameter: float):
        super().__init__('diameter', diameter)


class PadHole():
    def __init__(self, uuid: str, diameter: DrillDiameter,
                 vertices: List[Vertex]):
        self.uuid = uuid
        self.diameter = diameter
        self.vertices = vertices

    def __str__(self) -> str:
        ret = '(hole {} {}\n'.format(self.uuid, self.diameter)
        ret += indent_entities(self.vertices)
        ret += ')'
        return ret


class FootprintPad():
    def __init__(self, uuid: str, side: ComponentSide, shape: Shape,
                 position: Position, rotation: Rotation, size: Size,
                 radius: ShapeRadius, stop_mask: StopMaskConfig,
                 solder_paste: SolderPasteConfig,
                 copper_clearance: CopperClearance, function: PadFunction,
                 package_pad: PackagePadUuid, holes: List[PadHole]):
        self.uuid = uuid
        self.side = side
        self.shape = shape
        self.position = position
        self.rotation = rotation
        self.size = size
        self.radius = radius
        self.stop_mask = stop_mask
        self.solder_paste = solder_paste
        self.copper_clearance = copper_clearance
        self.function = function
        self.package_pad = package_pad
        self.holes = holes

    def __str__(self) -> str:
        ret = '(pad {} {} {}\n'.format(self.uuid, self.side, self.shape) +\
            ' {} {} {} {}\n'.format(self.position, self.rotation, self.size, self.radius) +\
            ' {} {} {} {}\n'.format(self.stop_mask, self.solder_paste, self.copper_clearance, self.function) +\
            ' {}\n'.format(self.package_pad)
        ret += indent_entities(self.holes)
        ret += ')'
        return ret


class Footprint():
    def __init__(self, uuid: str, name: Name, description: Description,
                 position_3d: Position3D, rotation_3d: Rotation3D):
        self.uuid = uuid
        self.name = name
        self.description = description
        self.position_3d = position_3d
        self.rotation_3d = rotation_3d
        self.pads: List[FootprintPad] = []
        self.models_3d: List[Footprint3DModel] = []
        self.polygons: List[Polygon] = []
        self.circles: List[Circle] = []
        self.texts: List[StrokeText] = []

    def add_pad(self, pad: FootprintPad) -> None:
        self.pads.append(pad)

    def add_3d_model(self, model: Footprint3DModel) -> None:
        self.models_3d.append(model)

    def add_polygon(self, polygon: Polygon) -> None:
        self.polygons.append(polygon)

    def add_circle(self, circle: Circle) -> None:
        self.circles.append(circle)

    def add_text(self, text: StrokeText) -> None:
        self.texts.append(text)

    def __str__(self) -> str:
        ret = '(footprint {}\n'.format(self.uuid) +\
            ' {}\n'.format(self.name) +\
            ' {}\n'.format(self.description) +\
            ' {} {}\n'.format(self.position_3d, self.rotation_3d)
        ret += indent_entities(sorted(self.models_3d))
        ret += indent_entities(self.pads)
        ret += indent_entities(self.polygons)
        ret += indent_entities(self.circles)
        ret += indent_entities(self.texts)
        ret += ')'
        return ret


class Package:
    def __init__(self, uuid: str, name: Name, description: Description,
                 keywords: Keywords, author: Author, version: Version,
                 created: Created, deprecated: Deprecated,
                 generated_by: GeneratedBy, categories: Iterable[Category],
                 assembly_type: AssemblyType):
        self.uuid = uuid
        self.name = name
        self.description = description
        self.keywords = keywords
        self.author = author
        self.version = version
        self.created = created
        self.deprecated = deprecated
        self.generated_by = generated_by
        self.categories = categories
        self.assembly_type = assembly_type
        self.pads: List[PackagePad] = []
        self.models_3d: List[Package3DModel] = []
        self.footprints: List[Footprint] = []
        self.approvals: List[str] = []

    def add_pad(self, pad: PackagePad) -> None:
        self.pads.append(pad)

    def add_footprint(self, footprint: Footprint) -> None:
        self.footprints.append(footprint)

    def add_3d_model(self, model: Package3DModel) -> None:
        self.models_3d.append(model)

    def add_approval(self, approval: str) -> None:
        self.approvals.append(approval)

    def __str__(self) -> str:
        ret = '(librepcb_package {}\n'.format(self.uuid) +\
            ' {}\n'.format(self.name) +\
            ' {}\n'.format(self.description) +\
            ' {}\n'.format(self.keywords) +\
            ' {}\n'.format(self.author) +\
            ' {}\n'.format(self.version) +\
            ' {}\n'.format(self.created) +\
            ' {}\n'.format(self.deprecated) +\
            ' {}\n'.format(self.generated_by) +\
            ''.join([' {}\n'.format(cat) for cat in self.categories]) +\
            ' {}\n'.format(self.assembly_type)
        ret += indent_entities(self.pads)
        ret += indent_entities(self.models_3d)
        ret += indent_entities(self.footprints)
        ret += indent_entities(sorted(self.approvals))
        ret += ')'
        return ret

    def serialize(self, output_directory: str) -> None:
        dir_path = path.join(output_directory, self.uuid)
        if not (path.exists(dir_path) and path.isdir(dir_path)):
            makedirs(dir_path)
        with open(path.join(dir_path, '.librepcb-pkg'), 'w') as f:
            f.write('1\n')
        with open(path.join(dir_path, 'package.lp'), 'w') as f:
            f.write(str(self))
            f.write('\n')
