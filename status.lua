-- This is a Lua script to install in Argo CD to improve
-- status reporting of SecurityPolicies
hs = {}
if obj.status ~= nil then
  if obj.status.accepted then
    hs.status = "Healthy"
  else
    hs.status = "Degraded"
  end
  hs.message = obj.status.message
  return hs
end

hs.status = "Progressing"
hs.message = "Waiting for reconciliation"
return hs
