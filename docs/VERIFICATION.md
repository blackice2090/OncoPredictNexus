# Release verification — 15 October 2026

- Production: https://oncopredictnexus.vercel.app
- GitHub and Vercel Git integration connected; a push-triggered production build reached Ready.
- GitHub CI passed for c3c13e4, including 19 Python tests, 12 frontend tests and the frontend build.
- A fresh clone independently passed the same tests and build; npm audit reported zero vulnerabilities.
- Fingerprinted research assets are preserved byte-for-byte with Git attributes. The frozen model SHA-256 is 049a37d94c50aca766da3ce0e103cbcf5dbbb696474a8627bea6087cd04a0acb.
- Public health, model metadata and three-drug inference were checked. SHAP additivity and original artifact parity are covered by the Python tests.
- The English production interface calculated the synthetic demonstration and downloaded its JSON with explanations. Its browser history survived reload. Arabic and English views loaded.
- Server-side visitor history returned 404. Separate browser stores and storage failures are covered by frontend tests.
- The automated browser security policy blocked opening the printable report's blob navigation. That browser opening and print rendering were not visually verified. Report generation, escaping and numerical preservation passed unit tests; a normal-browser print check remains a manual acceptance item.

These checks verify software behavior, not clinical validity or independent model performance. No model retraining or scientific result changes were performed for publication.
