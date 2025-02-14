using UnityEngine;

public class TrainController : MonoBehaviour
{
    public float rayLength = 1.0f;
    public Color rayColor = Color.green;

    void Update()
    {
        CastRays();
    }

    void CastRays()
    {
        // Train Dimensions
        float trainWidth = transform.localScale.x;
        float trainHeight = transform.localScale.y;
        float trainLength = transform.localScale.z;

        // Define ray positions (relative to train center)
        Vector3 frontCenter = transform.position + transform.forward * (trainLength / 2);
        Vector3 backCenter = transform.position - transform.forward * (trainLength / 2);

        // Offset positions for ray corners
        Vector3 offsetRight = transform.right * (trainWidth / 2);
        Vector3 offsetLeft = -transform.right * (trainWidth / 2);
        Vector3 offsetTop = transform.up * (trainHeight / 2);
        Vector3 offsetBottom = -transform.up * (trainHeight / 2);

        // Front Rays
        CastRay(frontCenter + offsetRight + offsetTop, transform.forward);
        CastRay(frontCenter + offsetLeft + offsetTop, transform.forward);
        CastRay(frontCenter + offsetRight + offsetBottom, transform.forward);
        CastRay(frontCenter + offsetLeft + offsetBottom, transform.forward);

        // Back Rays
        CastRay(backCenter + offsetRight + offsetTop, -transform.forward);
        CastRay(backCenter + offsetLeft + offsetTop, -transform.forward);
        CastRay(backCenter + offsetRight + offsetBottom, -transform.forward);
        CastRay(backCenter + offsetLeft + offsetBottom, -transform.forward);
    }

    void CastRay(Vector3 origin, Vector3 direction)
    {
        Debug.DrawRay(origin, direction * rayLength, rayColor);
        if (Physics.Raycast(origin, direction, out RaycastHit hit, rayLength))
        {
            Debug.Log("Train hit something: " + hit.collider.name);
        }
    }
}
