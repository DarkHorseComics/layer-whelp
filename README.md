### Whelp

Whelp is a recommendation engine for DarkHorseComics DHD/Dungeon, this charm deploys it!


# Overview
This charm provides the scaffolding for "Whelp"!

The main idea behind whelp deployment was to be as efficient as possible with the mitigation of internal resources. To this extent, a statefile is pulled from bucket storage instead of being regenerated on deploy. Also, this charm leverages  Juju "resources" in order to facilitate development, deployment, and scaling at a heightened level of security, portablilty, and reusability at no extra cost.


# Configuration

To deploy whelp, you must also pass it a config file 'whelp.yaml`.

    # whelp.yaml
    whelp:
      snowflake-address: "<snowflake-fqdn>"
      swift-bucket-url: "http://<swift-bucket>:5000/v2.0"
      swift-bucket-user: "bucket-user"
      swift-bucket-pass: "bucket-pass"  
      swift-bucket-tenant: "bucket-tenant"
      swift-container: "container"
      swift-object: "state.tar.gz"

# Usage

To deploy whelp you need to know the latest charmstore revision. If you do not have access to the DHC team on launchpad, please get that going on first. Following an invitation to launchpad.net/~dhc, you must then login to the charmstore - more on development practices [here](https://jujucharms.com/docs/devel/authors-charm-store), and then run `charm list -u dhc` to get the current revision number that should be usedfor deployment.

After you have the latest rev, go ahead and deploy the application.

    juju deploy cs:~dhc/whelp-<latest-rev-no> --config whelp.yaml


The configuration options will be listed on the charm store, however you will need to supply your own creds in whelp.yaml.

# Contact Information

James Beedy <jbeedy@darkhorse.com> / Cole Howard <coleh@darkhorse.com>

* layer-whelp - https://github.com/darkhorsecomics/layer-whelp.git
