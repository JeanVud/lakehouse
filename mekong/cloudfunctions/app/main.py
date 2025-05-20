import requests

def forward(request, to: str):
  payload = request.get_json(silent=True)
  resp = requests.post(
    url=f"http://10.0.64.9:5000/webhook/v1/event/handler/{to}",
    json=payload,
  )
  data = resp.json()
  return data

def forward_http_request_to_sep(request):
    return forward(request, to = 'sep')