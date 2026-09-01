% Lua control script (opaque to the ASP parser).
#script (lua)
local version = "1.0.0"
function main(prg)
  prg:ground({{"base", {}}})
  prg:solve()
end
#end.

p(a).
