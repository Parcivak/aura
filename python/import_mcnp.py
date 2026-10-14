import meshio as mesh
from f4enix.output.meshtal import Meshtal

tally_filepath = "../full-mcnp/"


meshtal = Meshtal("meshtal")
meshtal.readMesh()
