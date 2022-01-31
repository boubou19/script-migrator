from pprint import pprint
from test import text

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
        return f"""getModItem("{parts[0]}", "{parts[1][0]}", {quantity})"""
    elif len(parts) == 3:
        if parts[0]=="ore": #funny: some smartasses put : in the oredict name
            return f'"{parts[1]+":"+parts[2]}"'
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


def assembler_conv(string, fluid_present=False):
    # Assembler.addRecipe(<EnderZoo:blockConfusingCharge>, <minecraft:tnt>, <EnderZoo:confusingDust> * 4, 400, 16);
    if "Assembler.addRecipe" in string:
        strip_list = default_strip_list + ["Assembler.addRecipe"]
        new_string = replace(string, strip_list)
        elems = new_string.split(",")
        voltage = elems[-1]
        ticktime = elems[-2]
        fluid = "GT_Values.NF" if not fluid_present else elems[-3]
        output_delimiter = -3 if fluid_present else -2
        output = prepare_item(elems[0])
        inputs = "\n" + ",\n".join([prepare_item(x) for x in elems[1:output_delimiter]])

        return f"""GT_Values.RA.addAssemblerRecipe(new ItemStack[]{{{inputs}}},\n{fluid},\n{output},\n{ticktime}, {voltage});"""
    else:
        raise TypeError("not an assembler recipe")


def crafting_shaped_conv(string):
    if "recipes.addShaped" in string:
        strip_list = default_strip_list + ["recipes.addShaped"]
        new_string = replace(string, strip_list)
        elems = [prepare_item(elem) for elem in new_string.split(",")]
        output = elems[0]
        # inputs = "\n".join([",".join([elems[i:3*i+1]]) for i in range(1,4)])
        inputs = ",\n".join([",".join(elems[3 * (i - 1) + 1:3 * i + 1]) for i in range(1, 4)])

        return f"\naddShapedRecipe({output}, new Object[]{{\n{inputs}}});"
    else:
        raise TypeError("not a shaped crafting recipe")


def crafting_shapeless_conv(string):
    if "recipes.addShapeless" in string:
        strip_list = default_strip_list + ["recipes.addShapeless"]
        new_string = replace(string, strip_list)
        elems = [prepare_item(elem) for elem in new_string.split(",")]
        output = elems[0]
        # inputs = "\n".join([",".join([elems[i:3*i+1]]) for i in range(1,4)])
        inputs = ",\n".join(elems[1:])
        return f"\naddShapelessCraftingRecipe({output}, new Object[]{{\n{inputs}}});"
    else:
        raise TypeError("not a shapeless crafting recipe")


def extreme_crafting_conv(string):
    letters = [chr(i) for i in range(97, 123)]
    index = 0
    ingredients = set()
    mapping = dict()

    if "mods.avaritia.ExtremeCrafting.addShaped" in string:
        strip_list = default_strip_list + ["mods.avaritia.ExtremeCrafting.addShaped"]
        new_string = replace(string, strip_list)
        elems = [prepare_item(elem) for elem in new_string.split(",")]
        output = elems[0]
        del elems[0]
        for elem in elems:
            if not elem in ingredients:
                ingredients.add(elem)
                if elem == "null":
                    mapping["null"]=" "
                else:
                    mapping[elem] = letters[index]
                    index += 1

        recipe = [mapping[x] for x in elems]
        recipe =",\n".join(['"'+"".join(recipe[9*i:9*(i+1)])+'"' for i in range(len(recipe)//9)])
        recipe += ",\n"+",\n".join([f"""'{v}', {k}""" for k,v in mapping.items()])
        # inputs = "\n".join([",".join([elems[i:3*i+1]]) for i in range(1,4)])
        # inputs = ",\n".join(elems[1:])
        # print(inputs)
        return f"\nExtremeCraftingManager.getInstance().addRecipe({output},\n{recipe});"
    else:
        raise TypeError("not an extreme shaped crafting recipe")


def process_all(dic):
    mappings = {"addShaped": crafting_shaped_conv, "assembler": assembler_conv, "shapeless": crafting_shapeless_conv,
                "extreme_craft": extreme_crafting_conv}
    dic["val"] = [x.strip("val") for x in dic["val"]]
    val_list = sorted(
        [[val[:val.find("=")].replace(" ", ""), val[val.find("=") + 1:].strip(" ").strip(";")] for val in dic["val"]],
        key=lambda x: x[0], reverse=True)
    del dic["val"]
    # pprint(val_list)
    exceptions = []
    for recipe_type in dic.keys():
        for i, recipe in enumerate(dic[recipe_type]):
            reps = []
            for old, new in val_list:
                if old in recipe[recipe.find("("):]:
                    reps.append((old, new))

            for j, rep in enumerate(reps):
                old, new = rep
                recipe = recipe.replace(old, f"{{{j}}}")
            try:
                recipe = recipe.format(*[x[1] for x in reps])
                dic[recipe_type][i] = recipe
                print(mappings[recipe_type](recipe))
            except BaseException as e:
                exceptions.append((e, recipe))
                # print(e)
                # print("error: "+recipe)
    pprint(exceptions)


def main():
    test = text.split("\n")
    recipe = []
    blacklist = ["recipes.addShaped", "Assembler.addRecipe", "val", "recipes.addShapeless",
                 "mods.avaritia.ExtremeCrafting.addShaped"]
    results = {"assembler": [], "val": [], "addShaped": [], "shapeless": [], "extreme_craft": []}
    assembling = False
    val = False
    addShaped = False
    shapeless = False
    extreme_craft = False
    added = False
    for line in test:
        if line == "" or line.startswith("//") or line.startswith("recipes.remove"):
            continue

        # assembler recipe
        if line.startswith("Assembler.addRecipe"):
            assembling = True
            recipe.append(line)
            added = True

        # close assembler recipe
        if assembling == True and line.endswith(";"):
            if not added:
                recipe.append(line)
            assembling = False
            results["assembler"].append("".join(recipe))
            recipe = []
            added = False
            continue

        # val
        if line.startswith("val"):
            val = True
            recipe.append(line)
            added = True

        # close val
        if val == True and line.endswith(";"):
            if not added:
                recipe.append(line)
            val = False
            results["val"].append("".join(recipe))
            recipe = []
            added = False
            continue

        # addshaped recipes
        if line.startswith("recipes.addShaped"):
            addShaped = True
            recipe.append(line)
            added = True

        # close addshaped recipes
        if addShaped is True and line.endswith(";"):
            if not added:
                recipe.append(line)
            addShaped = False
            # print("".join(recipe))
            results["addShaped"].append("".join(recipe))
            recipe = []
            added = False
            continue

        # addshapeless recipes
        if line.startswith("recipes.addShapeless"):
            shapeless = True
            recipe.append(line)
            added = True

        # close addshaped recipes
        if shapeless == True and line.endswith(";"):
            if not added:
                recipe.append(line)
            shapeless = False
            # print("".join(recipe))
            results["shapeless"].append("".join(recipe))
            recipe = []
            added = False
            continue

        # avaritia recipes
        if line.startswith("mods.avaritia.ExtremeCrafting.addShaped"):
            extreme_craft = True
            recipe.append(line)
            added = True

        # close extreme crafting recipes
        if extreme_craft == True and line.endswith(";"):
            if not added:
                recipe.append(line)
            shapeless = False
            # print("".join(recipe))
            results["extreme_craft"].append("".join(recipe))
            recipe = []
            added = False
            continue

        # add line while it's not starting or ending
        if (val or assembling or addShaped or extreme_craft) and not line.endswith(";") and not all(
                [x in line for x in blacklist]) \
                and not added:
            recipe.append(line)
            added = False
            continue
        # unknown detection
        if "recipes" in line and not any([x in line for x in blacklist]):
            print("WARNING: " + line)

        added = False
    return results


# print(results["addShaped"][10])

# pprint(results["addShaped"])
# print(prepare_item("gregtech:gt.metaitem.01:32101"))
if __name__ == "__main__":
    results = main()
    process_all(results)
