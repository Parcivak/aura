//* This file is part of the MOOSE framework
//* https://mooseframework.inl.gov
//*
//* All rights reserved, see COPYRIGHT for full restrictions
//* https://github.com/idaholab/moose/blob/master/COPYRIGHT
//*
//* Licensed under LGPL 2.1, please see LICENSE for details
//* https://www.gnu.org/licenses/lgpl-2.1.html
#include "auraTestApp.h"
#include "auraApp.h"
#include "Moose.h"
#include "AppFactory.h"
#include "MooseSyntax.h"

InputParameters
auraTestApp::validParams()
{
  InputParameters params = auraApp::validParams();
  params.set<bool>("use_legacy_material_output") = false;
  params.set<bool>("use_legacy_initial_residual_evaluation_behavior") = false;
  return params;
}

auraTestApp::auraTestApp(const InputParameters & parameters) : MooseApp(parameters)
{
  auraTestApp::registerAll(
      _factory, _action_factory, _syntax, getParam<bool>("allow_test_objects"));
}

auraTestApp::~auraTestApp() {}

void
auraTestApp::registerAll(Factory & f, ActionFactory & af, Syntax & s, bool use_test_objs)
{
  auraApp::registerAll(f, af, s);
  if (use_test_objs)
  {
    Registry::registerObjectsTo(f, {"auraTestApp"});
    Registry::registerActionsTo(af, {"auraTestApp"});
  }
}

void
auraTestApp::registerApps()
{
  registerApp(auraApp);
  registerApp(auraTestApp);
}

/***************************************************************************************************
 *********************** Dynamic Library Entry Points - DO NOT MODIFY ******************************
 **************************************************************************************************/
// External entry point for dynamic application loading
extern "C" void
auraTestApp__registerAll(Factory & f, ActionFactory & af, Syntax & s)
{
  auraTestApp::registerAll(f, af, s);
}
extern "C" void
auraTestApp__registerApps()
{
  auraTestApp::registerApps();
}
