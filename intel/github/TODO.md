- Get enterprise info

- In github you can allow to bypass branch protections to everyone or just to indicated principals. In `analyze_results.py`, aroun line 152, you can see that the api only indicates with a boolean if everyone can bypass the protection. We should check if it's possible to get a list of allowed principals that can bypass it.

- Steal the secrets automatically