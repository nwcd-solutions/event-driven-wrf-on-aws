#!/usr/bin/env python3

import aws_cdk as cdk

from nwp.root import Root

app = cdk.App()

wx = Root(app, 'WRF')
cdk.Tags.of(wx).add("Purpose", "Event Driven Weather Forecast", priority=300)

app.synth()
