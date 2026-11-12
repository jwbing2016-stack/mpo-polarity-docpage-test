# LC Fiber Cable: Six Specifications to Check Before Ordering

An order for “LC fiber, 3 meters” leaves several decisions to the supplier. The connector may fit, yet the fiber type, polish, or number of strands may be wrong for the connection.

Before requesting a quote, turn that short description into a specification that identifies both endpoints and the cable between them. These six checks help buyers and installers order an LC fiber cable with fewer assumptions.

## 1. Confirm the connector at each end

LC describes a connector family. It does not identify the complete cable assembly.

Check the actual optical interface on the transceiver, equipment, or patch panel at both endpoints. An LC-to-LC cable has LC connectors at both ends; a connection between LC and SC interfaces needs a different assembly. Also record the end-face polish at each connection.

Put the two endpoints in the purchase request separately:

- **End A:** equipment or panel reference, connector, and polish.
- **End B:** equipment or panel reference, connector, and polish.

Photographs of the equipment labels and existing connections can help resolve missing information. Use them alongside the equipment documentation, especially when the replacement cable has no readable part number.

## 2. Match the fiber to the optical application

An LC connector does not tell you whether the cable contains single-mode or multimode fiber. OS2 is a single-mode category; OM3 and OM4 are multimode categories. Match the patch cord to the optical modules and the installed fiber channel.

Reach also depends on the application. For example, [Cisco specifies its SFP-10G-SR module](https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/data_sheet_c78-455693.html) for links up to 300 meters over OM3 and 400 meters over OM4. Those figures apply to the specified optical application and compliant channel, not to every cable with an LC connector.

Record the exact module part numbers and the fiber category already installed. Replacing a short patch cord does not change the rest of the channel.

For a specification that calls for single-mode duplex patching with LC UPC interfaces at both ends, Cablefam lists an [OS2 LC UPC to LC UPC duplex patch cord](https://cablefam.com/product/lc-upc-to-lc-upc-os2-duplex-patch-cord). Its connector format alone does not make it a substitute for a multimode assembly.

## 3. Check UPC or APC at every mating interface

Connector polish is a separate specification from connector shape and fiber category. A request that says only “LC single-mode” is incomplete when the mating interface requires a particular polish.

**Do not directly mate UPC and APC end faces.** [Fluke Networks explains](https://www.flukenetworks.com/blog/cabling-chronicles/101-series-what-apc-connector-and-how-do-i-test-it) that the mismatch can cause poor optical performance and damage the end faces.

Specify the required polish for End A and End B rather than asking for whichever option is available. Treat an unclear connector description as a question to resolve before ordering, rather than a detail for the installer to discover on site.

## 4. Confirm fiber count and polarity

Simplex and duplex describe different assemblies: simplex contains one fiber, while duplex contains two. Confirm which arrangement the equipment requires.

In a conventional two-fiber optical link, the transmit path must reach the receive path at the opposite end. Record the required fiber mapping through any intervening panels. Single-fiber bidirectional optics use a different arrangement and require the correct module pairing; do not assume every LC connection needs a duplex cord.

For an order that already specifies OM4, two fibers, and LC UPC at both ends, an [OM4 LC-to-LC duplex patch cord](https://cablefam.com/product/om4-lc-to-lc-fiber-patch-cord) is a configuration to evaluate against those requirements. Confirm the complete channel and equipment compatibility before selection.

## 5. Measure the route and check handling space

Measure the path the cable will follow through cable managers and into the ports. Rack-to-rack distance alone can miss vertical routing, turns, and service slack.

Before choosing a length, record:

- The routed distance and the agreed allowance for servicing.
- Clearance around connector boots and neighboring cables.
- Any moving tray or equipment that affects the route.
- The assembly manufacturer's minimum bend radius and handling limits.

State the length unit, measurement reference, and any required tolerance in the order. If a standard length does not suit the route, request availability for the needed length rather than assuming it can be supplied.

## 6. Specify jacket requirements and acceptance checks

Include the installation environment and the required jacket specification. If the project requires LSZH material, a particular fire classification, or supporting documents, list each requirement explicitly and ask the supplier to confirm it for the proposed assembly.

Agree on the acceptance checks before purchase as well. These may include connector end-face inspection, fiber mapping, and optical measurements required by the project. State any required test limits, wavelengths, report format, and identification labels rather than relying on an undefined “tested” claim.

[Corning's connector-cleaning guidance](https://www.corning.com/data-center/worldwide/en/home/knowledge-center/connector-cleaning-faqs.html) explains how contamination can increase insertion loss and reflections. Follow the connector manufacturer's inspection and cleaning instructions before mating.

## Turn the checks into a clear quotation request

The following is an illustrative request, not a universal specification or a statement of stock availability:

> Please quote 50 LC UPC-to-LC UPC duplex patch cords using OM4 50/125 μm fiber, 3 m nominal length, with an LSZH jacket. Please confirm the cable diameter, length measurement and tolerance, minimum bend radius, fiber mapping, applicable jacket documentation, and available optical test reports. The intended application is a 10GBASE-SR link; the exact transceiver models and channel layout will be supplied for compatibility review.

For a mixed order, use one line per configuration. Keep single-mode and multimode requirements separate, and include quantities, delivery destination, required delivery date, and any labeling instructions.

To discuss an LC fiber cable requirement, [contact Cablefam](https://cablefam.com/contact-us.html) with your endpoint details and specification list. Include the module part numbers, existing fiber category, connector polish, fiber count, routed length, and quantity so the proposed assembly can be checked against the intended connection.
