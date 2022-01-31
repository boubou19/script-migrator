from pprint import pprint
from test import text
from handlers import handler_assembler, handler_shaped_crafting,\
    handler_shapless_crafting, handler_extreme_shaped_crafting

default_strip_list = [" ", "[", "(", "<", ">", ")", "]", ";", "\n"]
wildcard_value = 32767


def process_all(dic):
    mappings = {"addShaped": handler_shaped_crafting.process, "assembler": handler_assembler.process,
                "shapeless": handler_shapless_crafting.process, "extreme_craft": handler_extreme_shaped_crafting}
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
    if len(exceptions):
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
