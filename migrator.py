from pprint import pprint
from test import text
from handlers import handler_assembler, handler_shaped_crafting, \
    handler_shapless_crafting, handler_extreme_shaped_crafting

default_strip_list = [" ", "[", "(", "<", ">", ")", "]", ";", "\n"]
wildcard_value = 32767

handlers = {"addShaped": handler_shaped_crafting,
            "assembler": handler_assembler,
            "shapeless": handler_shapless_crafting,
            "extreme_craft": handler_extreme_shaped_crafting}


def process_all(dic):
    mappings = {"addShaped": handler_shaped_crafting.process,
                "assembler": handler_assembler.process,
                "shapeless": handler_shapless_crafting.process,
                "extreme_craft": handler_extreme_shaped_crafting.process}

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
    blacklist = {handler_name: handler.discriminator for handler_name, handler in handlers.items()}
    blacklist["val"] = "val"

    results = {handler_name: [] for handler_name in blacklist.keys()}
    states = {handler_name: False for handler_name in blacklist.keys()}

    added = False
    for line in test:
        # skip useless lines
        if line == "" or line.startswith("//") or line.startswith("recipes.remove"):
            continue

        for handler_name in results.keys():

            # assembler recipe
            if line.startswith(blacklist[handler_name]):
                states[handler_name] = True
                recipe.append(line)
                added = True

            # close assembler recipe
            if states[handler_name] is True and line.endswith(";"):
                if not added:
                    recipe.append(line)
                states[handler_name] = False
                results[handler_name].append("".join(recipe))
                recipe = []
                added = False
                continue

        # add line while it's not starting or ending
        if (any([value for value in states.values()])) and not line.endswith(";") \
                and not all([x in line for x in blacklist.values()]) \
                and not added:
            recipe.append(line)
            added = False
            continue

        # unknown detection
        if "recipes" in line and not any([x in line for x in blacklist.values()]):
            print("WARNING: " + line)

        added = False
    return results


if __name__ == "__main__":
    results = main()
    process_all(results)
