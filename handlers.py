default_strip_list = [" ", "[", "(", "<", ">", ")", "]", ";", "\n"]
wildcard_value = 32767


def replace(string, L):
    new_string = string

    for elem in L:
        new_string = new_string.replace(elem, "")

    return new_string


def prepare_item(string):
    # "Translocator:translocator:1*2"
    # "gregtech:gt.metaitem.01:32101"
    parts = string.split(":")
    if len(parts) == 1:
        return string
    elif len(parts) == 2:
        # oredict string
        if parts[0] == "ore":
            return f'"{parts[1]}"'

        parts[1] = parts[1].split("*")
        if len(parts[1]) == 1:
            quantity = 1
        else:
            quantity = parts[1][1]

        # deal with fluid stacks
        if parts[0] == "liquid":
            return f"""FluidRegistry.getFluidStack({parts[1][0]}, {quantity})"""

        return f"""getModItem("{parts[0]}", "{parts[1][0]}", {quantity})"""
    elif len(parts) == 3:
        if parts[0] == "ore":  # funny: some smartasses put : in the oredict name
            return f'"{parts[1] + ":" + parts[2]}"'
        parts[2] = parts[2].split("*")
        if parts[2][-1] == "" or len(parts[2]) == 1:
            quantity = 1
        else:
            quantity = parts[2][-1]
        if "" == parts[2][0]:
            parts[2][0] = wildcard_value
        return f"""getModItem("{parts[0]}", "{parts[1]}", {quantity}, {parts[2][0]})"""
    else:
        raise ValueError("too many values in the item splitting: " + string)


class Handler:
    def __init__(self, discriminator):
        self.discriminator = discriminator
        self.strip_list = default_strip_list + [discriminator]

    def check_handler_appliable(self, string):
        return self.discriminator in string

    def process(self, string, **kwargs):
        if self.discriminator in string:
            new_string = replace(string, self.strip_list)
            elems = new_string.split(",")
            return self.parsing_logic(elems, **kwargs)
        else:
            raise TypeError(f"not a valid recipe for {self.discriminator}")

    def parsing_logic(self, elems, **kwargs):
        pass


class HandlerAssembler(Handler):
    def __init__(self):
        Handler.__init__(self, "Assembler.addRecipe")


    def parsing_logic(self, elems, **kwargs):
        elems = [prepare_item(elem) for elem in elems]
        fluid_present = kwargs["fluid_present"] if "fluid_present" in kwargs else False
        voltage = elems[-1]
        ticktime = elems[-2]
        print(elems[-3])
        fluid_present = "FluidRegistry.getFluidStack" in elems[-3]
        fluid = "GT_Values.NF" if not fluid_present else elems[-3]

        output_delimiter = -3 if fluid_present else -2
        output = elems[0]
        inputs = "\n" + ",\n".join([x for x in elems[1:output_delimiter]])

        return f"""GT_Values.RA.addAssemblerRecipe(new ItemStack[]{{{inputs}}},
        {fluid},
        {output},
        {ticktime},
        {voltage});"""


class HandlerShapedCrafting(Handler):
    def __init__(self):
        Handler.__init__(self, "recipes.addShaped")

    def parsing_logic(self, elems, **kwargs):
        elems = [prepare_item(elem) for elem in elems]
        output = elems[0]
        inputs = ",\n".join([",".join(elems[3 * (i - 1) + 1:3 * i + 1]) for i in range(1, 4)])

        return f"\naddShapedRecipe({output}, new Object[]{{\n{inputs}}});"


class HandlerShapelessCrafting(Handler):
    def __init__(self):
        Handler.__init__(self, "recipes.addShapeless")

    def parsing_logic(self, elems, **kwargs):
        elems = [prepare_item(elem) for elem in elems]
        output = elems[0]
        inputs = ",\n".join(elems[1:])
        return f"\naddShapelessCraftingRecipe({output}, new Object[]{{\n{inputs}}});"


class HandlerExtremeShapedCrafting(Handler):
    def __init__(self):
        Handler.__init__(self, "mods.avaritia.ExtremeCrafting.addShaped")

    def parsing_logic(self, elems, **kwargs):
        letters = [chr(i) for i in range(97, 123)]
        index = 0
        ingredients = set()
        mapping = dict()

        elems = [prepare_item(elem) for elem in elems]
        output = elems[0]
        del elems[0]
        for elem in elems:
            if elem not in ingredients:
                ingredients.add(elem)
                if elem == "null":
                    mapping["null"] = " "
                else:
                    mapping[elem] = letters[index]
                    index += 1

        recipe = [mapping[x] for x in elems]
        recipe = ",\n".join(['"' + "".join(recipe[9 * i:9 * (i + 1)]) + '"' for i in range(len(recipe) // 9)])
        recipe += ",\n" + ",\n".join([f"""'{v}', {k}""" for k, v in mapping.items()])
        return f"\nExtremeCraftingManager.getInstance().addRecipe({output},\n{recipe});"


handler_assembler = HandlerAssembler()
handler_shaped_crafting = HandlerShapedCrafting()
handler_shapless_crafting = HandlerShapelessCrafting()
handler_extreme_shaped_crafting = HandlerExtremeShapedCrafting()

