@unit
Feature: Extract postcode area

  Scenario: Extract postcode area from full postcode
    Given a dataset with the following rows
      | postcode:string |
      | SW1A 2AA        |
      | M1 1AE          |
    When I extract the postcode area from the full postcode
    Then the resulting dataset should include the following rows
      | postcode:string | postcode_area:string |
      | SW1A 2AA        | SW1A                 |
      | M1 1AE          | M1                   |

  Scenario: Handle invalid postcodes correctly
    Given a dataset with the following rows
      | postcode:string |
      | SW1A2AA         |
      | EC1A1BB         |
    When I extract the postcode area from the full postcode
    Then the resulting dataset should include the following rows
      | postcode:string | postcode_area:string |
      | SW1A2AA         | null                 |
      | EC1A1BB         | null                 |

  Scenario: Handle empty or null postcodes correctly
    Given a dataset with the following rows
      | postcode:string |
      |                 |
      | null            |
    When I extract the postcode area from the full postcode
    Then the resulting dataset should include the following rows
      | postcode:string | postcode_area:string |
      |                 | null                 |
      | null            | null                 |
