import Foundation
import Vision
import CoreImage

let args = CommandLine.arguments
guard args.count == 3, let ciImage = CIImage(contentsOf: URL(fileURLWithPath: args[1])) else {
    fputs("usage: subject_mask <in> <out.png>\n", stderr); exit(1)
}
let handler = VNImageRequestHandler(ciImage: ciImage)
let request = VNGenerateForegroundInstanceMaskRequest()
try handler.perform([request])
guard let result = request.results?.first else { fputs("no subject found\n", stderr); exit(2) }
let maskBuffer = try result.generateScaledMaskForImage(forInstances: result.allInstances, from: handler)
let mask = CIImage(cvPixelBuffer: maskBuffer)
let filter = CIFilter(name: "CIBlendWithMask")!
filter.setValue(ciImage, forKey: kCIInputImageKey)
filter.setValue(CIImage(color: CIColor.black).cropped(to: ciImage.extent), forKey: kCIInputBackgroundImageKey)
filter.setValue(mask, forKey: kCIInputMaskImageKey)
let ctx = CIContext()
try ctx.writePNGRepresentation(of: filter.outputImage!, to: URL(fileURLWithPath: args[2]),
                               format: .RGBA8, colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)
print("mask applied")
