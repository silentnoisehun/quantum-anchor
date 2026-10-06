import sys, os
sys.path.insert(0, os.getcwd())
import src.anchor_model as m
std = set(sys.stdlib_module_names)
loaded = {k.split(".")[0] for k in sys.modules}
extra = {t for t in loaded - std - {"src", "anchor_model"} if not t.startswith("_")}
print("non-stdlib:", extra if extra else "none")
assert not extra, f"unexpected non-stdlib import: {extra}"
print("clean: stdlib only")
