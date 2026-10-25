"""
Smart Sorting Conveyor Animation Engine
Includes Guaranteed Visuals & Logistics Timer
"""
import time
import traceback
import adsk.core
import adsk.fusion

app = adsk.core.Application.get()
ui = app.userInterface
handlers = []

def force_material_and_color(occ, mat_name, r, g, b, design):
    """Applies Physical Material and enforces Appearance color to guarantee visuals."""
    try:
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

def animate_conveyor(speed_delay, speed_level):
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design: return
        root = design.rootComponent

        try:
            weight_val = float(root.attributes.itemByName("ConveyorParams", "CargoWeight").value)
            L = float(root.attributes.itemByName("ConveyorParams", "ConveyorL").value)
            H = float(root.attributes.itemByName("ConveyorParams", "ConveyorH").value)
            W = float(root.attributes.itemByName("ConveyorParams", "ConveyorW").value)
            D = float(root.attributes.itemByName("ConveyorParams", "RollerD").value)
        except:
            ui.messageBox("Metrics missing. Generate Conveyor first.")
            return

        sort_right = (weight_val > 10.0)
        direction_label = "RIGHT" if sort_right else "LEFT"

        for occ in reversed(root.occurrences):
            if "Payload_Cargo" in occ.component.name:
                occ.deleteMe()

        box_x_size, box_y_size, box_z_size = 12.0, 8.0, 12.0
        spawn_x = 5.0 + (box_x_size / 2.0)
        spawn_y = (H + D/2.0) + (box_y_size / 2.0)
        spawn_z = 0.0

        roller_max_z = W / 2.0   
        roller_min_z = -W / 2.0  
        
        target_z = (roller_min_z + (box_z_size / 2.0)) if sort_right else (roller_max_z - (box_z_size / 2.0))

        travel_distance = (L - spawn_x) - 10.0 
        total_steps = max(40, int(travel_distance / 1.2))
        straight_steps = int(total_steps / 2)
        sort_steps = total_steps - straight_steps
        z_step = (target_z - spawn_z) / sort_steps 

        tb = adsk.fusion.TemporaryBRepManager.get()
        box_brep = tb.createBox(adsk.core.OrientedBoundingBox3D.create(
            adsk.core.Point3D.create(spawn_x, spawn_y, spawn_z), 
            adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0), box_x_size, box_y_size, box_z_size))
        
        mat = adsk.core.Matrix3D.create()
        box_occ = root.occurrences.addNewComponent(mat)
        box_occ.component.name = f"Payload_Cargo_{weight_val}kg_{direction_label}"
        
        base = box_occ.component.features.baseFeatures.add()
        base.startEdit()
        box_occ.component.bRepBodies.add(box_brep, base)
        base.finishEdit()
        
        # Apply the exact Oak Red Material with Wood-Colored RGB Fallback
        force_material_and_color(box_occ, "Oak, Red", 160, 105, 60, design)
        
        # FORCE UI REFRESH TO RENDER COLOR BEFORE MOVING
        viewport = app.activeViewport
        viewport.refresh()
        adsk.doEvents()

        # Animation Loop
        start_time = time.time()
        
        for i in range(total_steps):
            transform = box_occ.transform
            dx, dy, dz = 1.2, 0.0, (0.0 if i < straight_steps else z_step)

            vec = transform.translation
            vec.x += dx
            vec.y += dy
            vec.z += dz
            transform.translation = vec
            box_occ.transform = transform

            for joint in root.allAsBuiltJoints:
                if "Roller" in joint.name or (joint.occurrence1 and "Roller" in joint.occurrence1.name):
                    motion = joint.jointMotion
                    if motion and motion.jointMotionType == adsk.fusion.JointMotionTypes.RevoluteJointMotion:
                        motion.rotationValue += 0.25

            viewport.refresh()
            adsk.doEvents()
            time.sleep(speed_delay)
            
        end_time = time.time()
        
        report_msg = (
            f"✅ Sorting Complete!\n\n"
            f"📦 Cargo Weight: {weight_val} kg\n"
            f"🛤️ Route Taken: {direction_label}\n"
            f"⏩ Conveyor Speed: Level {speed_level}/10\n"
            f"⏱️ Total Travel Time: {round(end_time - start_time, 2)} seconds"
        )
        ui.messageBox(report_msg, "Simulation Report")

    except Exception as e: pass

class AnimatorExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args):
        try:
            inputs = args.command.commandInputs
            slider_val = inputs.itemById('speed_slider').valueOne
            animate_conveyor((11 - slider_val) * 0.01, slider_val)
        except: pass

class AnimatorDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args): adsk.terminate()

class AnimatorCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self): super().__init__()
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            inputs.addIntegerSliderCommandInput('speed_slider', 'Animation Speed', 1, 10, False)
            inputs.itemById('speed_slider').valueOne = 7 
            
            onExecute = AnimatorExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)
            onDestroy = AnimatorDestroyHandler()
            cmd.destroy.add(onDestroy)
            handlers.append(onDestroy)
        except: pass

def run(context):
    try:
        global handlers
        handlers.clear()
        cmdDef = ui.commandDefinitions.itemById('ConveyorAnimatorUI')
        if cmdDef: cmdDef.deleteMe()
        cmdDef = ui.commandDefinitions.addButtonDefinition('ConveyorAnimatorUI', 'Animate Conveyor', '')
        onCommandCreated = AnimatorCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        cmdDef.execute()
        adsk.autoTerminate(False)
    except: pass