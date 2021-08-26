import http.client
import json

conn = http.client.HTTPSConnection("api.ijingzhun.com")
payload = json.dumps([
  {
    "awbno": "07442557325",
    "carriercd": "KL"
  }
])
headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer dc791577-04b4-4a1d-8e65-ce048a65c2b0'
}
conn.request("POST", "/trace/airUploadBooking", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
