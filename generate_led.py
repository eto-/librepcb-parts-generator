"""
Generate THT LED packages.
"""
from math import acos, asin, degrees, sqrt
from os import path
from uuid import uuid4

from typing import Iterable, List, Optional

from common import format_ipc_dimension as fd
from common import init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Circle, Created, Deprecated, Description, Diameter, Fill, GeneratedBy, GrabArea,
    Height, Keywords, Layer, Name, Polygon, Position, Position3D, Rotation, Rotation3D, Value, Version, Vertex, Width
)
from entities.component import SignalUUID
from entities.device import ComponentPad, ComponentUUID, Device, PackageUUID
from entities.package import (
    AssemblyType, AutoRotate, ComponentSide, CopperClearance, DrillDiameter, Footprint, FootprintPad, LetterSpacing,
    LineSpacing, Mirror, Package, PackagePad, PackagePadUuid, PadFunction, PadHole, Shape, ShapeRadius, Size,
    SolderPasteConfig, StopMaskConfig, StrokeText, StrokeWidth
)

GENERATOR_NAME = 'librepcb-parts-generator (generate_led.py)'

lead_width = 0.5
pad_drill = 0.8
default_line_width = 0.2
pkg_text_height = 1.0


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_led.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        full_name:
            For example "SOIC127P762X120-16".
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


class LedConfig:
    def __init__(
        self,
        top_diameter: float,
        bot_diameter: float,
        lead_spacing: float,
        body_height: float,
        standoff: float,
        standoff_in_name: bool,
        body_color: str,
    ):
        self.top_diameter = top_diameter
        self.bot_diameter = bot_diameter
        self.lead_spacing = lead_spacing
        self.body_height = body_height
        self.standoff = standoff
        self.standoff_in_name = standoff_in_name
        self.body_color = body_color

        self.pkg_name = 'LED-THT-P{lead_spacing}D{top_diameter}H{body_height}{standoff_option}-{body_color}'.format(
            top_diameter=fd(top_diameter),
            body_height=fd(body_height),
            lead_spacing=fd(lead_spacing),
            standoff_option=('S' + fd(standoff)) if standoff_in_name else '',
            body_color=body_color.upper(),
        )
        self.pkg_description = \
            'Generic through-hole LED with {top_diameter:.2f} mm' \
            ' body diameter.\n\n' \
            'Body height: {body_height:.2f} mm.\n' \
            'Lead spacing: {lead_spacing:.2f} mm.\n' \
            'Standoff: {standoff:.2f} mm.\n' \
            'Body color: {body_color}.' \
            '\n\nGenerated with {generator}'.format(
                top_diameter=top_diameter,
                body_height=body_height,
                lead_spacing=lead_spacing,
                standoff=standoff,
                body_color=body_color,
                generator=GENERATOR_NAME,
            )

        self.dev_name = 'LED ⌀{top_diameter}x{body_height}{standoff_option}/{lead_spacing}mm {body_color}'.format(
            top_diameter=top_diameter,
            body_height=body_height,
            lead_spacing=lead_spacing,
            standoff_option=('+' + str(standoff)) if standoff_in_name else '',
            body_color=body_color,
        )
        self.dev_description = self.pkg_description


def generate_pkg(
    library: str,
    author: str,
    configs: Iterable[LedConfig],
    pkgcat: str,
    keywords: str,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'pkg'
    for config in configs:
        is_small = config.top_diameter < 5  # Small LEDs need adjusted footprints

        def _uuid(identifier: str) -> str:
            return uuid(category, config.pkg_name, identifier)

        uuid_pkg = _uuid('pkg')

        print('Generating {}: {}'.format(config.pkg_name, uuid_pkg))

        # Package
        package = Package(
            uuid=uuid_pkg,
            name=Name(config.pkg_name),
            description=Description(config.pkg_description),
            keywords=Keywords(keywords),
            author=Author(author),
            version=Version(version),
            created=Created(create_date or now()),
            deprecated=Deprecated(False),
            generated_by=GeneratedBy(''),
            categories=[Category(pkgcat)],
            assembly_type=AssemblyType.AUTO,
        )

        # Package pads
        package.add_pad(PackagePad(uuid=_uuid('pad-a'), name=Name('A')))
        package.add_pad(PackagePad(uuid=_uuid('pad-c'), name=Name('C')))

        # Footprint
        def _add_footprint(
            package: Package,
            name: Name,
            identifier_suffix: str,
            pad_size: Size,
        ) -> Footprint:
            footprint = Footprint(
                uuid=_uuid('footprint' + identifier_suffix),
                name=name,
                description=Description(''),
                position_3d=Position3D(0.0, 0.0, 0.0),
                rotation_3d=Rotation3D(0.0, 0.0, 0.0),
            )
            package.add_footprint(footprint)

            # Footprint pads
            for pad, factor in [('a', 1), ('c', -1)]:
                pad_uuid = _uuid('pad-{}'.format(pad))
                footprint.add_pad(FootprintPad(
                    uuid=pad_uuid,
                    side=ComponentSide.TOP,
                    shape=Shape.ROUNDED_RECT,
                    position=Position(config.lead_spacing / 2 * factor, 0),
                    rotation=Rotation(90),
                    size=pad_size,
                    radius=ShapeRadius(0.0 if pad == 'c' else 1.0),
                    stop_mask=StopMaskConfig.AUTO,
                    solder_paste=SolderPasteConfig.OFF,
                    copper_clearance=CopperClearance(0.0),
                    function=PadFunction.UNSPECIFIED,
                    package_pad=PackagePadUuid(pad_uuid),
                    holes=[PadHole(pad_uuid, DrillDiameter(pad_drill),
                                   [Vertex(Position(0.0, 0.0), Angle(0.0))])],
                ))

            return footprint

        def _add_vertical_footprint(
            package: Package,
            name: Name,
            identifier_suffix: str,
            pad_size: Size,
        ) -> None:
            footprint = _add_footprint(
                package=package,
                identifier_suffix=identifier_suffix,
                name=name,
                pad_size=pad_size,
            )

            # Now the interesting part: The circles with the flattened side.
            # For this, we use a polygon with a circle segment.
            def _add_flattened_circle(
                footprint: Footprint,
                identifier: str,
                layer: str,
                outer_radius: float,
                inner_radius: float,
                line_width: float,
                reduced: bool = False,
            ) -> None:
                """
                Generate a flattened circle. The flat side will be on the left.

                If outer_radius == inner_radius, then a circle will be created instead.

                If `reduced` is true, then a reduced version (only top and bottom
                circle segments) will be generated.

                """
                # Special case: If outer_radius == inner_radius, return a full circle.
                if outer_radius == inner_radius:
                    footprint.add_circle(Circle(
                        uuid=_uuid(identifier),
                        layer=Layer(layer),
                        width=Width(line_width),
                        position=Position(0, 0),
                        diameter=Diameter(outer_radius * 2),
                        fill=Fill(False),
                        grab_area=GrabArea(False),
                    ))
                    return

                # To calculate the y offset of the flat side, use Pythagoras
                y = sqrt(outer_radius ** 2 - inner_radius ** 2)

                # Now we can calculate the angle of the circle segment
                if reduced:
                    angle = degrees(2 * asin(inner_radius / outer_radius))
                else:
                    angle = 180 - degrees(acos(inner_radius / outer_radius))

                # Generate polygon
                if not reduced:
                    # Regular polygon with flattened side
                    polygon = Polygon(
                        uuid=_uuid(identifier),
                        layer=Layer(layer),
                        width=Width(line_width),
                        fill=Fill(False),
                        grab_area=GrabArea(False),
                    )
                    polygon.add_vertex(Vertex(Position(-inner_radius, -y), Angle(angle)))
                    polygon.add_vertex(Vertex(Position(outer_radius, 0), Angle(angle)))
                    polygon.add_vertex(Vertex(Position(-inner_radius, y), Angle(0)))
                    polygon.add_vertex(Vertex(Position(-inner_radius, -y), Angle(0)))
                    footprint.add_polygon(polygon)
                else:
                    # Reduced two-part polygon
                    for y, suffix in [(y, '-top'), (-y, '-bot')]:
                        polygon = Polygon(
                            uuid=_uuid(identifier + suffix),
                            layer=Layer(layer),
                            width=Width(line_width),
                            fill=Fill(False),
                            grab_area=GrabArea(False),
                        )
                        polygon.add_vertex(Vertex(Position(inner_radius, y), Angle(angle if y > 0 else -angle)))
                        polygon.add_vertex(Vertex(Position(-inner_radius, y), Angle(0)))
                        polygon.add_vertex(Vertex(Position(-inner_radius, y * 0.80), Angle(0)))
                        footprint.add_polygon(polygon)

            _add_flattened_circle(
                footprint,
                identifier='polygon-doc' + identifier_suffix,
                layer='top_documentation',
                outer_radius=config.bot_diameter / 2 - default_line_width / 2,
                inner_radius=config.top_diameter / 2 - default_line_width / 2,
                line_width=default_line_width,
            )
            _add_flattened_circle(
                footprint,
                identifier='polygon-legend' + identifier_suffix,
                layer='top_legend',
                outer_radius=config.bot_diameter / 2 + default_line_width / 2,
                inner_radius=config.top_diameter / 2 + default_line_width / 2,
                line_width=default_line_width,
                reduced=is_small,
            )

            # Courtyard
            courtyard_offset = (1.0 if config.bot_diameter >= 10.0 else 0.8) / 2
            pad_ring_x_bounds = config.lead_spacing / 2 + pad_size.height / 2
            _add_flattened_circle(
                footprint,
                identifier='polygon-courtyard' + identifier_suffix,
                layer='top_courtyard',
                outer_radius=max(config.bot_diameter / 2, pad_ring_x_bounds) + courtyard_offset,
                inner_radius=max(config.top_diameter / 2, pad_ring_x_bounds) + courtyard_offset,
                line_width=0.0,
            )

            # Text
            footprint.add_text(StrokeText(
                uuid=_uuid('text-name' + identifier_suffix),
                layer=Layer('top_names'),
                height=Height(1.0),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                align=Align('center bottom'),
                position=Position(0.0, (config.bot_diameter / 2) + 0.8),
                rotation=Rotation(0.0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
                value=Value('{{NAME}}'),
            ))
            footprint.add_text(StrokeText(
                uuid=_uuid('text-value' + identifier_suffix),
                layer=Layer('top_values'),
                height=Height(1.0),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                align=Align('center top'),
                position=Position(0.0, -(config.bot_diameter / 2) - 0.8),
                rotation=Rotation(0.0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
                value=Value('{{VALUE}}'),
            ))

        def _add_horizontal_footprint(
            package: Package,
            name: Name,
            identifier_suffix: str,
            pad_size: Size,
            body_height: float,
            body_offset: float,
        ) -> None:
            footprint = _add_footprint(
                package=package,
                identifier_suffix=identifier_suffix,
                name=name,
                pad_size=pad_size,
            )

            # Documentation outline
            polygon = Polygon(
                uuid=_uuid('polygon-doc' + identifier_suffix),
                layer=Layer('top_documentation'),
                width=Width(default_line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
            )
            inner_radius = config.top_diameter / 2 - default_line_width / 2
            outer_radius = config.bot_diameter / 2 - default_line_width / 2
            body_bottom_y = body_offset + default_line_width / 2
            body_middle_y = body_bottom_y + 1.0 - default_line_width
            body_top_y = body_bottom_y + body_height - inner_radius - default_line_width
            polygon.add_vertex(Vertex(Position(-inner_radius, body_middle_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(-inner_radius, body_top_y), Angle(-180)))
            polygon.add_vertex(Vertex(Position(inner_radius, body_top_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(inner_radius, body_middle_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(outer_radius, body_middle_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(outer_radius, body_bottom_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(-inner_radius, body_bottom_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(-inner_radius, body_middle_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(inner_radius, body_middle_y), Angle(0)))
            footprint.add_polygon(polygon)

            # Documentation leads
            for pad, factor in [('a', 1), ('c', -1)]:
                polygon = Polygon(
                    uuid=_uuid('polygon-doc-' + pad + identifier_suffix),
                    layer=Layer('top_documentation'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(False),
                )
                x0 = min((config.lead_spacing / 2 + lead_width / 2), config.top_diameter / 2) * factor
                x1 = (2 * (config.lead_spacing / 2) - x0 * factor) * factor
                polygon.add_vertex(Vertex(Position(x0, body_offset), Angle(0)))
                polygon.add_vertex(Vertex(Position(x1, body_offset), Angle(0)))
                polygon.add_vertex(Vertex(Position(x1, -lead_width / 2), Angle(0)))
                polygon.add_vertex(Vertex(Position(x0, -lead_width / 2), Angle(0)))
                polygon.add_vertex(Vertex(Position(x0, body_offset), Angle(0)))
                footprint.add_polygon(polygon)

            # Determine legend variant
            body_bottom_y -= default_line_width
            pad_legend_clearance = pad_size.width / 2 + default_line_width / 2 + 0.18
            split_legend = body_bottom_y < pad_legend_clearance

            # legend short
            if split_legend:
                polygon = Polygon(
                    uuid=_uuid('polygon-legend2' + identifier_suffix),
                    layer=Layer('top_legend'),
                    width=Width(default_line_width),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                )
                legend_x = config.lead_spacing / 2 - pad_legend_clearance
                polygon.add_vertex(Vertex(Position(-legend_x, body_bottom_y), Angle(0)))
                polygon.add_vertex(Vertex(Position(legend_x, body_bottom_y), Angle(0)))
                footprint.add_polygon(polygon)

            # legend outline
            polygon = Polygon(
                uuid=_uuid('polygon-legend' + identifier_suffix),
                layer=Layer('top_legend'),
                width=Width(default_line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
            )
            inner_radius = config.top_diameter / 2 + default_line_width / 2
            outer_radius = config.bot_diameter / 2 + default_line_width / 2
            body_bottom_silkscreen_x = config.lead_spacing / 2 + pad_legend_clearance
            body_bottom_silkscreen_y = max(body_bottom_y, pad_legend_clearance)
            body_middle_y += default_line_width
            if split_legend is False:
                polygon.add_vertex(Vertex(Position(-inner_radius, body_bottom_y), Angle(0)))
            elif body_bottom_silkscreen_x < inner_radius:
                polygon.add_vertex(Vertex(Position(-body_bottom_silkscreen_x, body_bottom_y), Angle(0)))
                polygon.add_vertex(Vertex(Position(-inner_radius, body_bottom_y), Angle(0)))
            else:
                polygon.add_vertex(Vertex(Position(-inner_radius, body_bottom_silkscreen_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(-inner_radius, body_top_y), Angle(-180)))
            polygon.add_vertex(Vertex(Position(inner_radius, body_top_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(inner_radius, body_middle_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(outer_radius, body_middle_y), Angle(0)))
            if split_legend is False:
                polygon.add_vertex(Vertex(Position(outer_radius, body_bottom_y), Angle(0)))
                polygon.add_vertex(Vertex(Position(-inner_radius, body_bottom_y), Angle(0)))
            elif body_bottom_silkscreen_x < outer_radius:
                polygon.add_vertex(Vertex(Position(outer_radius, body_bottom_y), Angle(0)))
                polygon.add_vertex(Vertex(Position(body_bottom_silkscreen_x, body_bottom_y), Angle(0)))
            else:
                polygon.add_vertex(Vertex(Position(outer_radius, body_bottom_silkscreen_y), Angle(0)))
            footprint.add_polygon(polygon)

            # Courtyard
            courtyard_offset = (1.0 if config.bot_diameter >= 10.0 else 0.8) / 2
            polygon = Polygon(
                uuid=_uuid('polygon-courtyard' + identifier_suffix),
                layer=Layer('top_courtyard'),
                width=Width(0.0),
                fill=Fill(False),
                grab_area=GrabArea(False),
            )
            inner_radius += courtyard_offset
            outer_radius += courtyard_offset
            body_middle_y += courtyard_offset
            body_bottom_y -= courtyard_offset
            courtyard_bottom_x = min(config.lead_spacing / 2 + pad_drill / 2 + courtyard_offset + 0.2, inner_radius)
            courtyard_bottom_y = -pad_drill / 2 - courtyard_offset - 0.2
            polygon.add_vertex(Vertex(Position(-inner_radius, body_bottom_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(-inner_radius, body_top_y), Angle(-180)))
            polygon.add_vertex(Vertex(Position(inner_radius, body_top_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(inner_radius, body_middle_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(outer_radius, body_middle_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(outer_radius, body_bottom_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(courtyard_bottom_x, body_bottom_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(courtyard_bottom_x, courtyard_bottom_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(-courtyard_bottom_x, courtyard_bottom_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(-courtyard_bottom_x, body_bottom_y), Angle(0)))
            polygon.add_vertex(Vertex(Position(-inner_radius, body_bottom_y), Angle(0)))
            footprint.add_polygon(polygon)

            # Text
            footprint.add_text(StrokeText(
                uuid=_uuid('text-name' + identifier_suffix),
                layer=Layer('top_names'),
                height=Height(1.0),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                align=Align('center top'),
                position=Position(0.0, -1.27),
                rotation=Rotation(0.0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
                value=Value('{{NAME}}'),
            ))
            footprint.add_text(StrokeText(
                uuid=_uuid('text-value' + identifier_suffix),
                layer=Layer('top_values'),
                height=Height(1.0),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                align=Align('center top'),
                position=Position(0.0, -3.0),
                rotation=Rotation(0.0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
                value=Value('{{VALUE}}'),
            ))

        # Add footprints
        _add_vertical_footprint(
            package,
            name=Name('Vertical'),
            identifier_suffix='',
            pad_size=Size(1.4, 1.4),
        )
        if not is_small:
            _add_vertical_footprint(
                package,
                name=Name('Vertical, Large Pads'),
                identifier_suffix='-large',
                pad_size=Size(2.5, 1.3),
            )
        _add_horizontal_footprint(
            package,
            name=Name('Horizontal, 0.5 mm Offset'),
            identifier_suffix='-h050',
            pad_size=Size(1.4, 1.4),
            body_height=config.body_height,
            body_offset=0.5,
        )
        _add_horizontal_footprint(
            package,
            name=Name('Horizontal, 2.54 mm Offset'),
            identifier_suffix='-h254',
            pad_size=Size(1.4, 1.4),
            body_height=config.body_height,
            body_offset=2.54,
        )
        _add_horizontal_footprint(
            package,
            name=Name('Horizontal, 7.62 mm Offset'),
            identifier_suffix='-h762',
            pad_size=Size(1.4, 1.4),
            body_height=config.body_height,
            body_offset=7.62,
        )

        package.serialize(path.join('out', library, category))


def generate_dev(
    library: str,
    author: str,
    configs: Iterable[LedConfig],
    cmpcat: str,
    keywords: str,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'dev'
    for config in configs:
        def _uuid(identifier: str) -> str:
            return uuid(category, config.dev_name, identifier)

        uuid_dev = _uuid('dev')

        print('Generating {}: {}'.format(config.dev_name, uuid_dev))

        device = Device(
            uuid=uuid_dev,
            name=Name(config.dev_name),
            description=Description(config.dev_description),
            keywords=Keywords(keywords),
            author=Author(author),
            version=Version(version),
            created=Created(create_date or now()),
            deprecated=Deprecated(False),
            generated_by=GeneratedBy(''),
            categories=[Category(cmpcat)],
            component_uuid=ComponentUUID('2b24b18d-bd95-4fb4-8fe6-bce1d020ead4'),
            package_uuid=PackageUUID(uuid('pkg', config.pkg_name, 'pkg')),
        )
        device.add_pad(ComponentPad(
            pad_uuid=uuid('pkg', config.pkg_name, 'pad-a'),
            signal=SignalUUID('f1467b5c-cc7d-44b4-8076-d729f35b3a6a'),
        ))
        device.add_pad(ComponentPad(
            pad_uuid=uuid('pkg', config.pkg_name, 'pad-c'),
            signal=SignalUUID('7b023430-b68f-403a-80b8-c7deb12e7a0c'),
        ))

        device.serialize(path.join('out', library, category))


if __name__ == '__main__':
    configs = []  # type: List[LedConfig]

    # Generic LEDs
    #
    # Commonly used LED dimensions were determined by looking at various LED
    # datasheets. The bottom diameter, body height and standoff height vary
    # between the many different LEDs since there's no standard and because
    # the the specified tolerances are huge (>1mm). However, for these generic
    # packages we just use some average dimensions for simplicity. For exact
    # dimensions, a separate package needs to be created for each LED model.
    #
    # Note: The standoff specifies the distance between the bottom of the
    #       LED body and the surface of the PCB.
    configs.append(LedConfig(3.00, 3.80, 2.54, 4.5, 1.0, False, 'Clear'))
    configs.append(LedConfig(3.00, 3.80, 2.54, 4.5, 5.0, True, 'Clear'))
    configs.append(LedConfig(5.00, 5.80, 2.54, 8.7, 1.0, False, 'Clear'))
    configs.append(LedConfig(5.00, 5.80, 2.54, 8.7, 5.0, True, 'Clear'))

    generate_pkg(
        library='LibrePCB_Base.lplib',
        author='Danilo B.',
        configs=configs,
        pkgcat='9c36c4be-3582-4f27-ae00-4c1229f1e870',
        keywords='led,tht',
        version='0.1',
        create_date='2022-02-26T00:06:03Z',
    )
    generate_dev(
        library='LibrePCB_Base.lplib',
        author='U. Bruhin',
        configs=configs,
        cmpcat='70421345-ae1d-4fed-aa60-e7619524b97f',
        keywords='led,tht',
        version='0.1',
        create_date='2022-08-31T11:18:33Z',
    )

    save_cache(uuid_cache_file, uuid_cache)
