New options for data processing activities:

#. Go to *Privacy > Master Data > Activities* and create one.

#. Give it a name, such as *Sending mass mailings to customers*.

#. Go to tab *Consent* and choose one option in *Ask subjects for consent*:

   * *Manual* tells the activity that you will want to create and send the
     consent requests manually, and only provides some helpers for you to
     be able to batch-generate them.

   * *Automatic* enables this module's full power: send all consent requests
     to selected partners automatically, every day and under your demand.

#. When you do this, all the consent-related options appear. Configure them:

   * A smart button tells you how many consents have been generated, and lets you
     access them.

   * Choose one *Email template* to send to subjects. This email itself is what
     asks for consent, and it gets recorded, to serve as a proof that it was sent.
     The module provides a default template that should be good for most usage
     cases; and if you create one directly from that field, some good defaults
     are provided for your comfortability.

   * *Subjects filter* defines what partners will be elegible for inclusion in
     this data processing activity.

   * You can enable *Accepted by default* if you want to assume subjects
     accepted their data processing. You should possibly consult your
     lawyer to use this.

   * You can choose a *Server action* (developer mode only) that will
     be executed whenever a new non-draft consent request is created,
     or when its acceptance status changes.

     This module supplies a server action by default, called
     *Update partner's opt out*, that syncs the acceptance status with the
     partner's *Elegible for mass mailings* option.

#. Click on *Generate consent requests* link to create new consent requests.

   * If you chose *Manual* mode, all missing consent request are created as
     drafts, and nothing else is done now.

   * If you chose *Automatic* mode, also those request e-mails are enqueued
     and, when the mail queue is cleared, they will be set as *Sent*.

#. You will be presented with the list of just-created consent requests.
   See below.

New options for consent requests:

#. Access the consent requests by either:

   * Generating new consent requests from a data processing activity.

   * Pressing the *Consents* smart button in a data processing activity.

   * Going to *Privacy > Privacy > Consents*.

#. A consent will include the partner, the activity, the acceptance status,
   and the request state.

#. You can manually ask for consent by pressing the button labeled as
   *Ask for consent*.

#. All consent requests and responses are recorded in the mail thread below.
