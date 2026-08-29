# Troubleshooting

## Backend exits immediately

Run:

`systemctl status vexora --no-pager -l`

Then:

`journalctl -u vexora -n 120 --no-pager`

Check the local endpoint:

`curl -v http://127.0.0.1:6000/health`

If this endpoint is unavailable, Nginx cannot fix the problem. The backend
must be repaired first.

## Nginx returns 502

A 502 normally means the upstream application is not accepting connections.
Check port 6000 and the systemd service before changing Nginx.

`ss -lntp | grep ':6000 '` 

`systemctl is-active vexora`

`curl http://127.0.0.1:6000/health`

## Certificate fails

Port 80 must be reachable from the public Internet for HTTP-01. If another
service owns port 80, standalone Certbot cannot complete the challenge.

For IP certificates, use a Certbot version that supports ACME IP certificate
issuance. The installer refuses to create a fake certificate.

## Public shop opens but admin redirects

That is expected until the administrator authenticates at `/admin/login`.
The customer route never requires admin login.
