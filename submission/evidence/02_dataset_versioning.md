# Dataset versioning evidence

Capture:

~~~text
type data\VERSION
type data\manifest.json
git rev-parse --show-toplevel
git log --oneline --decorate -10
~~~

On Mac/Linux use cat instead of type. Confirm the root is the extracted project directory; do not run git commands from its parent.
