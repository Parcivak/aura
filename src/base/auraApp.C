#include "auraApp.h"
#include "Moose.h"
#include "AppFactory.h"
#include "ModulesApp.h"
#include "MooseSyntax.h"

InputParameters
auraApp::validParams()
{
  InputParameters params = MooseApp::validParams();
  params.set<bool>("use_legacy_material_output") = false;
  params.set<bool>("use_legacy_initial_residual_evaluation_behavior") = false;
  return params;
}

auraApp::auraApp(const InputParameters & parameters) : MooseApp(parameters)
{
  auraApp::registerAll(_factory, _action_factory, _syntax);
}

auraApp::~auraApp() {}

void
auraApp::registerAll(Factory & f, ActionFactory & af, Syntax & syntax)
{
  ModulesApp::registerAllObjects<auraApp>(f, af, syntax);
  Registry::registerObjectsTo(f, {"auraApp"});
  Registry::registerActionsTo(af, {"auraApp"});

  /* register custom execute flags, action syntax, etc. here */
}

void
auraApp::registerApps()
{
  registerApp(auraApp);
}

/***************************************************************************************************
 *********************** Dynamic Library Entry Points - DO NOT MODIFY ******************************
 **************************************************************************************************/
extern "C" void
auraApp__registerAll(Factory & f, ActionFactory & af, Syntax & s)
{
  auraApp::registerAll(f, af, s);
}
extern "C" void
auraApp__registerApps()
{
  auraApp::registerApps();
}
