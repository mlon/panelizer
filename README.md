# Panel Tools

Web hosted tools to make building mlon eurorack panels easier:

- Creating appropriately sized SVG's following the mlon design language and containing predefined symbols for pots/jacks/nuts/LEDs etc. for easy editing in Inkscape.
- Converting SVGs to KiCad PCBs for manufacturing

More details on [panels.mlon.com](https://panels.mlon.com/)

## Developing

Open the devcontainer using VS Code, then start the flask server with 

```bash
flask --app panelizer --debug run
```