# Zola themes

All the community themes for Zola.

## Adding your theme

Follow the guidelines on the [documentation](https://www.getzola.org/documentation/themes/creating-a-theme/).

Once this is done, do a pull request to this repository adding your theme as a git submodule.

Themes are updated semi-regularly and all themes in this repo will be featured on the themes page of the Zola site.

## Generating themes site

Clone this repo and run `git submodule update --init --recursive`.

You will need python3 and the requirements listed in `requirements.txt` installed.

If you are a Nix user and flakes are available, you can use `flake.nix`.

To generate the markdown pages:

```bash
$ python generate_docs.py DESTINATION_FOLDER
```

Note that this will erase `DESTINATION_FOLDER` first so be careful.

## Updating all themes

```bash
$ git submodule update --remote --merge
```
