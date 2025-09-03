import anvil.email
import anvil.server

# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
# Here is an example - you can replace it with your own:
#
# @anvil.server.callable
# def say_hello(name):
#   print("Hello, " + name + "!")
#   return 42
#

@anvil.server.callable
def show_record(idate, ponumb, relnumb, series):
  # Send yourself an email each time feedback is submitted
  anvil.email.send(#to="noreply@anvil.works", # Change this to your email address and remove the #!
    subject=f"Feedback from {ponumb}",
    text=f"""
                   
  A new person has filled out the feedback form!

  Date: {idate}
  PO Number: {ponumb}
  Rel Number: {relnumb}
  Series: {series}
  """)
