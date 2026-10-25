"""
Parametric Conveyor API Generator for Fusion 360
Master Version: Guaranteed RGB Appearance, Payload Cleanup & Validation Limits.
"""
import math
import traceback
import adsk.core
import adsk.fusion

app = adsk.core.Application.get()
ui = app.userInterface
handlers = []

def get_inputs(inputs):
    L = inputs.itemById('L').value
    W = inputs.itemById('W').value
    H = inputs.itemById('H').value
    D = inputs.itemById('D').value
    P = inputs.itemById('P').value
    S = inputs.itemById('S').value
    G = inputs.itemById('G').value
    guards = inputs.itemById('guards').value
    weight_input = inputs.itemById('weight')
    weight = weight_input.value if weight_input else 12.0
    
    errs = []
    # Internal Fusion 360 dimensions are evaluated in cm (10mm = 1cm)
    if not (79.9 <= L <= 200.1): errs.append(f"- Conveyor length (L): {L*10:.0f} mm (Allowed: 800-2000 mm)")
    if not (29.9 <= W <= 60.1): errs.append(f"- Conveyor width (W): {W*10:.0f} mm (Allowed: 300-600 mm)")
    if not (49.9 <= H <= 90.1): errs.append(f"- Frame height (H): {H*10:.0f} mm (Allowed: 500-900 mm)")
    if not (3.9 <= D <= 8.1): errs.append(f"- Roller diameter (D): {D*10:.0f} mm (Allowed: 40-80 mm)")
    if not (7.9 <= P <= 15.1): errs.append(f"- Roller spacing (P): {P*10:.0f} mm (Allowed: 80-150 mm)")
    if not (49.9 <= S <= 100.1): errs.append(f"- Support-leg spacing (S): {S*10:.0f} mm (Allowed: 500-1000 mm)")
    if guards and not (-0.1 <= G <= 15.1): errs.append(f"- Side-guard height (G): {G*10:.0f} mm (Allowed: 0-150 mm)")

    return (max(1.0, L), max(1.0, W), max(1.0, H), max(1.0, D), max(1.0, P), max(1.0, S), max(0.0, G), guards, weight), errs

def clear_old_conveyors(design):
    root = design.rootComponent
    for i in range(root.occurrences.count - 1, -1, -1):
        occ = root.occurrences.item(i)
        name = occ.component.name.upper()
        if "CONVEYOR" in name or "PREVIEW" in name or "FRAME" in name or "ROLLER" in name or "LEG" in name or "GUARD" in name or "PAYLOAD" in name:
            occ.deleteMe()

def inject_brep(comp, temp_brep, name, design):
    try:
        if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
            base = comp.features.baseFeatures.add()
            base.startEdit()
            body = comp.bRepBodies.add(temp_brep, base)
            base.finishEdit()
        else:
            body = comp.bRepBodies.add(temp_brep)
        body.name = name
        return body
    except: return None

def force_material_and_color(occ, mat_name, r, g, b, design):
    """Applies Physical Material and enforces Appearance color to guarantee visuals."""
    try:
        # 1. Try to set exact Physical Material
        mat = design.materials.itemByName(mat_name)
        if not mat:
            for lib in app.materialLibraries:
                try:
                    m = lib.materials.itemByName(mat_name)
                    if m:
                        mat = design.materials.addByCopy(m, mat_name)
                        break
                except: pass
        if mat:
            for body in occ.component.bRepBodies:
                body.material = mat

        # 2. Guarantee Visual Color (Appearance) as a fallback
        app_name = f"Custom_Color_{r}_{g}_{b}"
        appearance = design.appearances.itemByName(app_name)
        if not appearance:
            lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
            if lib:
                base = lib.appearances.itemByName("Paint - Enamel (Glossy) (White)")
                if not base: base = lib.appearances.item(0)
                appearance = design.appearances.addByCopy(base, app_name)
                prop = appearance.appearanceProperties.itemByName("Color")
                if prop:
                    prop.value = adsk.core.Color.create(r, g, b, 255)
        if appearance:
            occ.appearance = appearance
    except: pass

def build_conveyor(vals, design, is_preview=False):
    L, W, H, D, P, S, G, guards, weight = vals
    root = design.rootComponent
    tb = adsk.fusion.TemporaryBRepManager.get()
    clear_old_conveyors(design)

    mat3d = adsk.core.Matrix3D.create()
    conv_occ = root.occurrences.addNewComponent(mat3d)
    conv_occ.component.name = "Parametric_Conveyor_Assembly" if not is_preview else "PREVIEW_GHOST"
    conv_comp = conv_occ.component

    # 1. FRAME 
    frame_occ = conv_comp.occurrences.addNewComponent(mat3d)
    frame_occ.component.name = "Frame"
    box_L = tb.createBox(adsk.core.OrientedBoundingBox3D.create(
        adsk.core.Point3D.create(L/2, H - 2.5, W/2), adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0), L, 5.0, 2.0))
    box_R = tb.createBox(adsk.core.OrientedBoundingBox3D.create(
        adsk.core.Point3D.create(L/2, H - 2.5, -W/2), adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0), L, 5.0, 2.0))
    
    inject_brep(frame_occ.component, box_L, "Frame_Left", design)
    inject_brep(frame_occ.component, box_R, "Frame_Right", design)
    
    force_material_and_color(frame_occ, "Stainless Steel", 200, 200, 200, design)
    if not is_preview: frame_occ.isGrounded = True

    # 2. ROLLERS 
    margin = 5.0
    avail = L - (margin * 2)
    if avail > 0:
        count = math.floor(avail / P) + 1
        for i in range(count):
            x = margin + (i * P)
            cyl = tb.createCylinderOrCone(adsk.core.Point3D.create(x, H, -W/2), D/2, adsk.core.Point3D.create(x, H, W/2), D/2)
            r_occ = conv_comp.occurrences.addNewComponent(mat3d)
            r_occ.component.name = f"Roller_{i+1}"
            inject_brep(r_occ.component, cyl, "Roller_Body", design)
            
            force_material_and_color(r_occ, "Steel", 50, 50, 50, design)

            if not is_preview:
                j_input = conv_comp.asBuiltJoints.createInput(r_occ, frame_occ)
                j_input.geometry = adsk.fusion.JointGeometry.createByPoint(adsk.core.Point3D.create(x, H, 0))
                j_input.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
                conv_comp.asBuiltJoints.add(j_input)

    # 3. LEGS 
    if avail > 0:
        count = math.floor(avail / S) + 1
        for i in range(count):
            x = margin + (i * S)
            leg_1 = tb.createBox(adsk.core.OrientedBoundingBox3D.create(
                adsk.core.Point3D.create(x, H/2, W/2 - 1), adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0), 4.0, H, 4.0))
            leg_2 = tb.createBox(adsk.core.OrientedBoundingBox3D.create(
                adsk.core.Point3D.create(x, H/2, -W/2 + 1), adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0), 4.0, H, 4.0))

            l_occ1 = conv_comp.occurrences.addNewComponent(mat3d)
            inject_brep(l_occ1.component, leg_1, "Leg_Body", design)
            force_material_and_color(l_occ1, "Steel, Paint Finish, Blue", 25, 30, 80, design)

            l_occ2 = conv_comp.occurrences.addNewComponent(mat3d)
            inject_brep(l_occ2.component, leg_2, "Leg_Body", design)
            force_material_and_color(l_occ2, "Steel, Paint Finish, Blue", 25, 30, 80, design)

    # 4. GUARDS 
    if guards and G > 0:
        g1 = tb.createBox(adsk.core.OrientedBoundingBox3D.create(
            adsk.core.Point3D.create(L/2, H + G/2, W/2 + 1), adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0), L, G, 2.0))
        g2 = tb.createBox(adsk.core.OrientedBoundingBox3D.create(
            adsk.core.Point3D.create(L/2, H + G/2, -W/2 - 1), adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0), L, G, 2.0))
            
        g_occ1 = conv_comp.occurrences.addNewComponent(mat3d)
        inject_brep(g_occ1.component, g1, "Guard_Body", design)
        force_material_and_color(g_occ1, "ABS Plastic", 220, 220, 220, design)

        g_occ2 = conv_comp.occurrences.addNewComponent(mat3d)
        inject_brep(g_occ2.component, g2, "Guard_Body", design)
        force_material_and_color(g_occ2, "ABS Plastic", 220, 220, 220, design)

    try:
        root.attributes.add("ConveyorParams", "CargoWeight", str(weight))
        root.attributes.add("ConveyorParams", "ConveyorL", str(L))
        root.attributes.add("ConveyorParams", "ConveyorH", str(H))
        root.attributes.add("ConveyorParams", "ConveyorW", str(W))
        root.attributes.add("ConveyorParams", "RollerD", str(D))
    except: pass

class ConveyorInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args):
        try:
            inputs = args.inputs
            L, W, H = inputs.itemById('L'), inputs.itemById('W'), inputs.itemById('H')
            D, P, S = inputs.itemById('D'), inputs.itemById('P'), inputs.itemById('S')
            G, guards = inputs.itemById('G'), inputs.itemById('guards')
            preset = inputs.itemById('preset')

            if args.input.id in ['L', 'W', 'H', 'D', 'P', 'S', 'G', 'guards']:
                preset.listItems.item(3).isSelected = True

            if args.input.id == 'preset':
                idx = args.input.selectedItem.index
                if idx == 0: 
                    L.expression, W.expression, H.expression = '800 mm', '300 mm', '500 mm'
                    D.expression, P.expression, S.expression = '40 mm', '100 mm', '500 mm'
                    G.expression, guards.value = '40 mm', True
                elif idx == 1: 
                    L.expression, W.expression, H.expression = '1200 mm', '450 mm', '700 mm'
                    D.expression, P.expression, S.expression = '50 mm', '100 mm', '600 mm'
                    G.expression, guards.value = '80 mm', True
                elif idx == 2: 
                    L.expression, W.expression, H.expression = '2000 mm', '600 mm', '900 mm'
                    D.expression, P.expression, S.expression = '60 mm', '120 mm', '700 mm'
                    G.expression, guards.value = '150 mm', True
        except: pass

class ConveyorPreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args):
        try:
            design = adsk.fusion.Design.cast(app.activeProduct)
            vals, errs = get_inputs(args.command.commandInputs)
            if not errs:
                build_conveyor(vals, design, is_preview=True)
                args.isValidResult = True 
            else:
                args.isValidResult = False
        except: pass

class ConveyorExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args):
        try:
            design = adsk.fusion.Design.cast(app.activeProduct)
            vals, errs = get_inputs(args.command.commandInputs)
            if errs:
                ui.messageBox("OUT OF RANGE ERROR:\n\n" + "\n".join(errs), "Validation Error")
                args.executeFailed = True
                return
            build_conveyor(vals, design, is_preview=False)
            app.activeViewport.refresh()
        except: pass

class ConveyorDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args): adsk.terminate()

class ConveyorCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            preset_input = inputs.addDropDownCommandInput('preset', 'Configuration', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            preset_input.listItems.add('Config A - Compact (800x300x500)', False)
            preset_input.listItems.add('Config B - Medium (1200x450x700)', True)
            preset_input.listItems.add('Config C - Large (2000x600x900)', False)
            preset_input.listItems.add('Custom Dimensions', False)

            inputs.addValueInput('L', 'Length (L)', 'mm', adsk.core.ValueInput.createByString('1200 mm'))
            inputs.addValueInput('W', 'Width (W)', 'mm', adsk.core.ValueInput.createByString('450 mm'))
            inputs.addValueInput('H', 'Height (H)', 'mm', adsk.core.ValueInput.createByString('700 mm'))
            inputs.addValueInput('D', 'Roller Diameter (D)', 'mm', adsk.core.ValueInput.createByString('50 mm'))
            inputs.addValueInput('P', 'Roller Spacing (P)', 'mm', adsk.core.ValueInput.createByString('100 mm'))
            inputs.addValueInput('S', 'Support Spacing (S)', 'mm', adsk.core.ValueInput.createByString('600 mm'))
            inputs.addValueInput('G', 'Guard Height (G)', 'mm', adsk.core.ValueInput.createByString('80 mm'))
            inputs.addBoolValueInput('guards', 'Include Side Guards', True, '', True)
            inputs.addFloatSpinnerCommandInput('weight', 'Cargo Weight (kg)', '', 1.0, 100.0, 1.0, 12.0)

            onInput = ConveyorInputChangedHandler()
            cmd.inputChanged.add(onInput)
            handlers.append(onInput)
            onPreview = ConveyorPreviewHandler()
            cmd.executePreview.add(onPreview)
            handlers.append(onPreview)
            onExecute = ConveyorExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)
            onDestroy = ConveyorDestroyHandler()
            cmd.destroy.add(onDestroy)
            handlers.append(onDestroy)
        except: pass

def run(_context: str):
    try:
        global handlers
        handlers.clear()
        cmdDef = ui.commandDefinitions.itemById('ConveyorGeneratorUI')
        if cmdDef: cmdDef.deleteMe()
        cmdDef = ui.commandDefinitions.addButtonDefinition('ConveyorGeneratorUI', 'Generate Conveyor', '')
        onCommandCreated = ConveyorCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        cmdDef.execute()
        adsk.autoTerminate(False)
    except: pass