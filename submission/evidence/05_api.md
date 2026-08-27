# API evidence

Start the API, then capture actual responses for:

~~~text
GET /health
POST /predict with valid trip JSON
POST /predict with blank text
POST /predict with malformed JSON
~~~

Use `reports/api_test.md` as the recorded response source after running the API test. Do not claim the dynamic request ID/latency without actual output.
